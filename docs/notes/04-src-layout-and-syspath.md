# `src/` Layout ve `sys.path`

## Soru

Kodu neden `src/` klasörünün içine koyuyoruz? Repo kökünde `lastfm_etl/` olsa ne
değişirdi — somut teknik bir sonucu var mı, yoksa sadece düzen meselesi mi?

Cevap: somut teknik sonucu var. Düzen meselesi değil.

## Barış önce ne sandı

İki yanlış varsayım vardı:

1. `src/` klasörünün estetik/konvansiyon meselesi olduğu — "dosyalar dağılmasın diye".
   Değil. `sys.path`'in davranışını değiştiren fonksiyonel bir karar.
2. `src/` klasörünün kendisinin bir Python paketi olduğu. Değil — `src/` **hiçbir zaman**
   import edilmez, `sys.path`'e girmez ve içinde `__init__.py` bulunmaz. Sadece bir
   duvar. Kurulan paketin adı `lastfm_etl`'dir, `src.lastfm_etl` değil.

## Önce: `sys.path` nedir

`sys.path`, Python'un modül ararken bakacağı **klasörlerin sıralı listesidir**. Düz bir
Python listesi — çalışma zamanında okunabilir, hatta değiştirilebilir.

```python
import sys
for p in sys.path:
    print(p)
```

Tipik bir çıktı (kısaltılmış):

```
                                  <- bulundugun klasor (cwd)
/usr/lib/python313.zip
/usr/lib/python3.13               <- stdlib
/usr/lib/python3.13/lib-dynload   <- C ile yazilmis stdlib modulleri
/home/user/.venv/lib/python3.13/site-packages   <- pip ile kurulanlar
```

Liste şu kaynaklardan bu sırayla doldurulur:

| Sıra | Kaynak | Açıklama |
|---|---|---|
| 1 | Script dizini veya cwd | Aşağıdaki tabloda detaylı |
| 2 | `PYTHONPATH` ortam değişkeni | Varsa, `:` (Windows'ta `;`) ile ayrılmış klasörler |
| 3 | Standart kütüphane | Python kurulumunun kendi modülleri |
| 4 | `site-packages` | `pip install` ile kurulan her şey buraya iner |

**Kritik olan sıra.** Python ilk eşleşeni alır ve durur. Yani 1. sıradaki bir dosya,
4. sıradaki kurulu paketi **gölgeler**. Bu notun tamamı bu tek cümlenin sonuçlarından
ibaret.

### Import gerçekte nasıl çalışır

`sys.path` tarama işinin sadece bir parçası. Tam akış:

1. `sys.modules` sözlüğüne bakılır — modül daha önce import edildiyse oradan döner.
   Bu yüzden bir modül, kaç kez import edilirse edilsin **bir kez** çalıştırılır.
2. Değilse `sys.meta_path` üzerindeki "finder" nesneleri sırayla denenir. Sonuncusu
   `PathFinder`'dır ve asıl `sys.path`'e bakan odur.
3. Modül bulunursa bir "loader" onu yükler, çalıştırır ve `sys.modules`'e koyar.

Pratikte 1. maddeyi bilmek yeter: **import edilen kod bir kez çalışır**, ve o an modül
seviyesindeki her satır işletilir. Bu, `__init__.py`'de ne yazılıp yazılmayacağının
temel sebebidir (bkz. not 06).

## Temel mekanizma: `sys.path[0]`

`sys.path` listesinin **ilk** elemanı özeldir, çünkü aramada ilk sırada gelir. Bu
eleman nasıl çalıştırdığına bağlıdır:

| Çalıştırma şekli | `sys.path[0]` |
|---|---|
| `python script.py` | `script.py`'nin bulunduğu klasör |
| `python -m paket` | cwd (bulunduğun klasör) |
| `python -c "..."` | cwd |
| `python` (REPL) | cwd |
| `pytest` (varsayılan `prepend` import modu) | rootdir / `conftest.py`'nin klasörü |

Ortak nokta: **repo kökü neredeyse her zaman `sys.path`'e girer.** Karar bu gerçeğin
üzerine kurulu.

## İki layout

```
flat layout                    src layout
repo/                          repo/
├── lastfm_etl/                ├── src/
│   └── __init__.py            │   └── lastfm_etl/
├── tests/                     │       └── __init__.py
└── pyproject.toml             ├── tests/
                               └── pyproject.toml
```

| | flat | src |
|---|---|---|
| Repo kökü `sys.path`'te mi | evet | evet |
| Kökün içinde `lastfm_etl` var mı | **evet** | hayır |
| `import lastfm_etl` neyi bulur | kaynak ağacındaki klasörü | sadece **kurulu** paketi |
| Kurulum olmadan import | çalışır | `ModuleNotFoundError` |

`src/` klasörü `sys.path`'e hiç girmediği için, altındaki paket ancak kurulumla
görünür hâle gelir.

## Doğrulama deneyi

```bash
mkdir -p /tmp/flatdemo/demo
echo "VALUE = 'kaynak agacindan geldim'" > /tmp/flatdemo/demo/__init__.py
cd /tmp/flatdemo && python -c "import demo; print(demo.VALUE)"
# -> kaynak agacindan geldim   (hicbir kurulum yapilmadi)

mkdir -p /tmp/srcdemo/src/demo
echo "VALUE = 'kaynak agacindan geldim'" > /tmp/srcdemo/src/demo/__init__.py
cd /tmp/srcdemo && python -c "import demo; print(demo.VALUE)"
# -> ModuleNotFoundError: No module named 'demo'
```

İkinci komutun hata vermesi **başarıdır**. src layout'un sağladığı korumanın tamamı
o hatadır.

## Asıl kazanç: test edilen artifact = dağıtılan artifact

Flat layout'ta sessizce oluşan senaryo:

| Adım | Ne olur | Fark edilir mi |
|---|---|---|
| 1 | `pyproject.toml`'da bir alt paket (`lastfm_etl.transform`) listelenmemiş | hayır |
| 2 | Testler yeşil — çünkü kaynak ağacından import ediyorlar | hayır |
| 3 | CI yeşil | hayır |
| 4 | `pip install .` → `ModuleNotFoundError: lastfm_etl.transform` | **evet, en geç noktada** |

Test ettiğin şey ile dağıttığın şey iki ayrı nesne. src layout bunları zorla aynı
nesne yapar: test etmek için önce kurmak zorundasın, dolayısıyla paketleme hatası
ilk `pytest`'te ortaya çıkar.

Bu soyut bir risk değil — Lambda'ya eksik paket göndermenin bedeli, deploy sonrası
CloudWatch'ta `ImportError` görmektir.

## İkincil kazanç: kök isim alanı temiz kalır

Repo kökü `sys.path`'te olduğu için, kökteki **her** klasör ve `.py` dosyası
top-level modül adına dönüşür:

- Kökte `tests/` varsa → `import tests` çözülebilir
- Kökte `utils.py` varsa → `import utils` çözülebilir
- Kökte `logging.py` varsa → stdlib'in `logging`'ini **gölgeler**

Sonuncusu teşhis etmesi en zor hata tiplerinden biridir: hata mesajı stdlib'i
işaret eder ama suçlu senin dosyandır. src layout kökü boşaltarak bu yüzeyi kapatır.

## Bedeli

src layout bedavaya gelmiyor: geliştirmeye başlamadan önce `pip install -e .`
(editable install) yapmak zorundasın. Flat layout'ta bu adım atlanabiliyordu.

Sürtünme bir kez ödenir, paketleme hatası ise her deploy'da patlar. Takas bu.

## Alternatif — flat layout ölü mü

Hayır. Django, pandas, NumPy hâlâ flat layout kullanıyor. Sebebi teknik değil
tarihsel: bu projeler src layout yaygınlaşmadan önce doğdu ve taşımanın maliyeti
faydasından yüksek.

Kaynak notu: src layout tercihi **PyPA Packaging Guide'ın tavsiyesidir**, bir PEP
veya spesifikasyon değil. Zorunluluk yok, yaygın modern pratik var.
<https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/>

## Junior tuzağı

"Testler geçiyor, demek ki paketleme doğru." Flat layout'ta bu çıkarım geçersizdir —
testler paketleme konfigürasyonuna hiç bakmadan geçebilir.

## Prod'da ne kırılır

CI aylarca yeşil kalır. Bir gün yeni bir alt paket eklenir, `pyproject.toml`
güncellenmez, wheel eksik çıkar. Local'de ve CI'da hiçbir belirti yok. Hata
üretimde, ilk çağrıda, `ImportError` olarak görünür.

## Mülakat cevabı

> "Neden src layout?"

Import'un kaynak ağacından kazara çözülmesini engellemek için. Böylece test ettiğin
artifact, kullanıcının kuracağı artifact ile aynı olur. Bedeli editable install
zorunluluğu, kazancı paketleme hatalarının `pip install` yerine ilk testte çıkması.

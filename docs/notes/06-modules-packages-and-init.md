# Modül, Paket, `__init__.py` ve İsimlendirme

## Terimler — dört ayrı şey

Python'da "paket" kelimesi dört farklı anlamda kullanılıyor ve karışıklığın kaynağı bu.

| Terim | Nedir | Örnek |
|---|---|---|
| **Modül** (module) | Tek bir `.py` dosyası | `config.py` → `import config` |
| **Paket** (package) | Modül içeren, import edilebilir bir klasör | `lastfm_etl/` → `import lastfm_etl` |
| **Dağıtım** (distribution) | PyPI'dan indirilen kurulabilir arşiv | `pip install lastfm-etl` |
| **Alt paket** (subpackage) | Paket içindeki paket | `lastfm_etl.extract` |

Bir dağıtım 0, 1 veya N tane import edilebilir paket içerebilir. Bire bir eşleşme
**garanti değildir**.

## Dağıtım adı ve import adı: iki ayrı isim alanı

| | Dağıtım adı | Import adı |
|---|---|---|
| Nerede geçer | `pip install X`, PyPI, `pyproject.toml` → `[project] name` | `import X`, klasör adı |
| Kim yorumlar | Paket yöneticisi (pip, uv) | Python yorumlayıcısı |
| İzinli karakterler | harf, rakam, `-`, `_`, `.` | harf, rakam, `_` |
| Büyük/küçük harf | önemsiz (normalize edilir) | **önemli** |
| Rakamla başlayabilir mi | evet | hayır |

Sektörden örnekler — ikisinin farklı olması istisna değil, normal:

| `pip install` | `import` |
|---|---|
| `scikit-learn` | `sklearn` |
| `Pillow` | `PIL` |
| `beautifulsoup4` | `bs4` |
| `PyYAML` | `yaml` |
| `python-dateutil` | `dateutil` |
| `opencv-python` | `cv2` |
| `attrs` | `attr` **ve** `attrs` (ikisi de) |

### Dağıtım adı normalizasyonu — PEP 503

Dağıtım adları karşılaştırılmadan önce normalize edilir:

1. Küçük harfe çevrilir
2. Ardışık `-`, `_`, `.` karakterleri tek `-`'e indirilir

Yani `scikit-learn`, `Scikit_Learn`, `scikit.learn` ve `SCIKIT---LEARN` PyPI için
**aynı** dağıtımdır. Import adında böyle bir hoşgörü yoktur — `import Sklearn` çalışmaz.

### Tire neden import adında olamaz

```python
import lastfm-pipeline
```

Bu satır `ModuleNotFoundError` **vermez**. `SyntaxError` verir.

Sebep: Python satırı çalıştırmadan önce **derlemek** zorunda. Tokenizer `lastfm`, `-`,
`pipeline` diye üç token üretir; `import` bir tanımlayıcı bekler, `-` görünce parse
başarısız olur.

Pratik sonucu — aşağıdaki kod seni kurtarmaz:

```python
try:
    import lastfm-pipeline
except ImportError:
    ...
```

`SyntaxError` **derleme** zamanında, `try` bloğu ise **çalışma** zamanında devreye
girer. Dosya hiç derlenmediği için `except` satırına asla ulaşılmaz.

| Hata | Ne zaman | Yakalanabilir mi |
|---|---|---|
| `SyntaxError` | derleme (parse) | hayır — dosya hiç çalışmaz |
| `ModuleNotFoundError` | çalışma zamanı | evet |

Tire içeren bir klasör teknik olarak `importlib.import_module("lastfm-pipeline")` ile
string üzerinden yüklenebilir. Yani "çalışan ama kimsenin normal syntax'la
kullanamayacağı" bir paket. Bu bir çözüm değil, semptom.

### Bu projedeki karar

| Rol | Değer |
|---|---|
| Dağıtım adı | `lastfm-etl` |
| Import adı | `lastfm_etl` |
| Klasör | `src/lastfm_etl/` |

Klasör adı import adıyla **birebir aynı** olmak zorunda.

PEP 8 paket adlarında underscore'u "discouraged" der. Buna rağmen `lastfm_etl`
seçildi: alternatifi `lastfmetl` ve okunabilirlik kaybı, PEP 8'in yumuşak tavsiyesinden
ağır bastı. `typing_extensions`, `importlib_metadata` gibi underscore'lu paketler
ekosistemde yaygın — kural mutlak değil.

---

## `__init__.py`

### Ne işe yarar

Bir klasörün **"ben bir Python paketiyim"** beyanıdır. İki işi vardır:

1. Klasörü normal (regular) bir pakete dönüştürmek
2. Paketin **public API'sini** tanımlamak

### Ne zaman çalışır

Paket ilk import edildiğinde, **bir kez**. İçindeki modül seviyesindeki her satır o an
işletilir.

```python
import lastfm_etl.extract.client
```

Bu tek satır sırayla şunları çalıştırır:

1. `lastfm_etl/__init__.py`
2. `lastfm_etl/extract/__init__.py`
3. `lastfm_etl/extract/client.py`

Yani **alt modülü import etmek, üstteki tüm `__init__.py`'leri çalıştırır.** Bu, aşağıdaki
"ne yazılmaz" bölümünün tek sebebidir.

Sonraki `import` çağrıları `sys.modules` cache'inden döner — dosya tekrar çalışmaz.

### Zorunlu mu — PEP 420

Python 3.3'ten önce zorunluydu. `__init__.py` olmayan klasör paket sayılmazdı.

**PEP 420** (Python 3.3, 2012) *namespace packages* kavramını getirdi: `__init__.py`
olmayan klasörler de import edilebilir hâle geldi.

| | Regular package | Namespace package |
|---|---|---|
| `__init__.py` | var | yok |
| `sys.path`'te birden fazla yerde bulunursa | ilki kazanır | hepsi **birleşir** |
| `__file__` özniteliği | var | yok |
| Ne zaman kullanılır | normal durum | tek bir isim altında ayrı ayrı dağıtılan paketler |

Namespace package'ın gerçek kullanım alanı dar: `zope.*`, `google.cloud.*` gibi farklı
ekiplerin bağımsız yayınladığı ama ortak bir isim altında toplanan paketler.

### Zorunlu değilse neden hâlâ yazıyoruz

| Sebep | Açıklama |
|---|---|
| Açık niyet | "Burası bir paket" beyanı, tesadüf değil |
| Sessiz birleşme | Namespace package'lar `sys.path`'te aynı isimde iki klasör bulursa **birleşir**. Teşhisi zor, sürprizli davranış |
| Build araçları | setuptools auto-discovery namespace paketlerde tuhaflaşabilir; paket eksik wheel'lar bu yüzden çıkar |
| API kapısı | Public API'yi tanımlayacak bir yer gerekir |

Kısacası: namespace package bir özellik değil, **özel bir kullanım senaryosu**. Varsayılan
olarak `__init__.py` yazılır.

### Boş `__init__.py` normal mi

Evet. Boş bırakmak, "burası bir paket ama henüz dışa açılan bir şey yok" demenin en dürüst
hâlidir. Zorla doldurmak yanlıştır.

### İçine ne yazılır

**1. Public API re-export**

```python
from lastfm_etl.extract.client import LastfmClient

__all__ = ["LastfmClient"]
```

Kullanıcı `from lastfm_etl.extract.client import LastfmClient` yerine
`from lastfm_etl import LastfmClient` yazabilir. Kazanç: iç dosya yapısını değiştirmekte
özgür kalırsın — kullanıcının import satırı bozulmaz.

**2. `__all__`**

`__all__`, `from paket import *` yazıldığında neyin geleceğini belirler. Asıl değeri
belgeleyici olmasıdır: "bunlar public, gerisi iç detay." Linter'lar (ruff) da bunu okur.

**3. Lazy import — PEP 562**

```python
def __getattr__(name: str):
    if name == "HeavyThing":
        from lastfm_etl.heavy import HeavyThing
        return HeavyThing
    raise AttributeError(name)
```

Ağır bir bağımlılığı (pandas gibi) sadece gerçekten kullanılınca yüklemek için. CLI
başlangıç süresini kısaltır. Erken optimizasyon yapma — gerçek bir yavaşlık ölçtüğünde
başvur.

### İçine ne YAZILMAZ — import-time side effect

Bunlar `__init__.py`'de olmamalı:

| Yasak | Neden |
|---|---|
| Dosya okuma / yazma | Paketi import etmek diske dokunmamalı |
| Ağ isteği | `import` bir HTTP çağrısı yapıyorsa test edilemez hâle gelir |
| Veritabanı bağlantısı | Aynı sebep |
| `settings = Settings()` | Env değişkeni eksikse **import** patlar |
| Logging konfigürasyonu | Kütüphanenin uygulamanın log ayarlarını ezmesi |
| Ağır bağımlılık import'u | `import pandas` her şeyi yavaşlatır |

En sinsi olanı `settings = Settings()`. Sonucu şudur: `.env` dosyası yoksa
`import lastfm_etl` satırı hata verir. Testler çalışmaz, `--help` çalışmaz, hatta
`ruff` bile bazı durumlarda takılır. Hata mesajı da import satırını gösterir — asıl
sebebi bulmak zaman alır.

Bu konu ROADMAP'te ayrı bir alt adım olarak duruyor: **2.4 — import-time yan etkisi**.
Oraya geldiğimizde bu notun bu bölümü işe yarayacak.

Genel kural: **import etmek ucuz ve yan etkisiz olmalı. İş, fonksiyon çağrılınca yapılır.**

---

## `__main__.py` ve `if __name__ == "__main__"`

Sık karıştırılan iki ayrı mekanizma.

### `if __name__ == "__main__":`

Her modülün `__name__` adında bir özniteliği vardır:

| Nasıl çalıştırıldı | `__name__` değeri |
|---|---|
| `python dosya.py` | `"__main__"` |
| `import dosya` | `"dosya"` |

Bu blok "bu dosya doğrudan çalıştırıldıysa şunu yap" demektir. Import edildiğinde
çalışmaz — yani bir dosya hem kütüphane hem script olabilir.

### `__main__.py`

Bir **paketin** doğrudan çalıştırılmasını sağlar:

```
src/lastfm_etl/
├── __init__.py
└── __main__.py
```

```bash
python -m lastfm_etl
```

Bu komut `lastfm_etl/__main__.py` dosyasını çalıştırır. `python -m pytest`,
`python -m http.server`, `python -m pip` hep bu mekanizmadır.

| | `__init__.py` | `__main__.py` |
|---|---|---|
| Ne zaman çalışır | paket **import** edilince | paket `python -m` ile **çalıştırılınca** |
| Zorunlu mu | hayır (ama yazılır) | hayır — sadece `-m` desteği isteniyorsa |

Adım 6'da (orkestrasyon) buraya döneceğiz.

---

## Bu projedeki mevcut durum

```
src/
└── lastfm_etl/
    └── __init__.py     (bos)
```

Alt paketler (`extract/`, `transform/`, `load/`) **bilinçli olarak açılmadı.** Hangi
modüllerin var olacağı Adım 1'in (veriyi tanı) çıktısıdır. Gerçek payload görülmeden
klasör yapısı kurmak, tahmine dayalı mimari demektir.

### `utils/` klasörü hakkında

İlk denemede `src/lastfm-pipeline/utils/` diye bir klasör açılmıştı. Silindi.

`utils` sektörde bilinen bir anti-pattern'dır. Sebebi: ismi hiçbir şey söylemez, bu
yüzden **her şey** oraya gider. Altı ay sonra `utils.py` içinde retry mantığı, tarih
biçimlendirme, S3 yolu üretimi ve bir logging yardımcısı yan yana durur — birbirleriyle
hiç ilgisi olmayan dört şey.

Testi basit: *bir dosyanın adı, içine neyin girip neyin girmeyeceğini söylemeli.*
`utils` bu testi geçemez. `paths.py`, `retry.py`, `timeparse.py` geçer.

---

## Junior tuzağı

Klasör yapısını en başta, kod yazmadan önce eksiksiz kurmak. Boş klasörler:

- Git tarafından **hiç görülmez** (git dosyaları takip eder, klasörleri değil)
- Gerçek veriyi görmeden alınmış mimari kararları donduruyormuş gibi hissettirir
- `utils/`, `helpers/`, `common/` gibi çöp kutusu isimlerini davet eder

## Prod'da ne kırılır

`__init__.py` içinde config yükleyen bir paket, bir gün CI'da `.env` olmadığı için
**test toplama aşamasında** patlar. Hata mesajı `ImportError` olur ve test kodunu
gösterir, gerçek sebebi (eksik env değişkeni) değil. Teşhis saatler alır.

## Mülakat cevabı

> "`__init__.py` ne işe yarar, hâlâ gerekli mi?"

Bir klasörü regular package yapar ve paketin public API'sini tanımlar. PEP 420'den beri
teknik olarak zorunlu değil — `__init__.py` olmayan klasörler namespace package olur.
Ama namespace package `sys.path`'te aynı isimli klasörleri sessizce birleştirir ve build
araçlarında sürprizler çıkarır, o yüzden özel bir ihtiyaç yoksa regular package
kullanılır. İçine ağır import veya yan etkili kod konmaz: import etmek ucuz olmalı.

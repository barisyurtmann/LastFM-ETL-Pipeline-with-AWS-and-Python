# 22 — Paket, `__init__.py` ve bir modülün public arayüzü

> **Kısa cevap** — `__init__.py` ne işe yarar, içine ne yazılır?
>
> 1. Bir klasörü **paket** yapar ve `import` edildiğinde **çalışan koddur** — boş bir
>    dosya değil, paketin giriş kapısı.
> 2. İçine yazılan `from ... import ...` satırları paketin **public arayüzünü** tanımlar:
>    çağıran taraf iç dosya adlarını bilmek zorunda kalmaz.
> 3. **Exception sınıfları da o arayüzün parçasıdır** — çünkü onları `raise` eden modül
>    değil, `except` eden çağıran taraf import eder.

---

## 1. Neden

Bu bilinmezse iki şey olur: ya `__init__.py` boş bırakılır ve her çağrı yeri iç dosya
yollarına (`lastfm_etl.extract.api`) bağlanır — dosyayı yeniden adlandırdığın gün on yerde
düzeltme çıkar; ya da içine her şey doldurulur ve paket import etmek yavaşlar, karşılıklı
import hataları başlar.

---

## 2. Modül, paket, `__init__.py`

| Terim | Tanım |
|---|---|
| **Modül** | Tek bir `.py` dosyası. `config.py` → `lastfm_etl.config` |
| **Paket** | İçinde modüller barındıran bir klasör. `extract/` → `lastfm_etl.extract` |
| **`__init__.py`** | Paketin klasöründeki özel dosya. Paket **ilk import edildiğinde çalışır** |

`__init__.py`'nin en çok yanlış bilinen tarafı: bu bir **işaret dosyası değil, çalışan
koddur**. `import lastfm_etl.extract` yazdığın anda Python o dosyayı baştan sona
yürütür — tıpkı normal bir `.py` gibi.

> Python 3.3'ten beri `__init__.py` olmadan da bir klasör import edilebilir (buna
> *namespace package* denir). Ama o yol paylaşılan namespace'ler için tasarlandı;
> sıradan bir projede `__init__.py` yazmak hâlâ doğru olandır — aksi halde paketin
> arayüzünü tanımlayacak bir yer kalmaz.

---

## 3. `__init__.py`'nin dört işi

| # | İş | Bizde |
|---|---|---|
| 1 | Klasörü paket yapmak | `extract/__init__.py` var |
| 2 | Paket import edilince çalışacak kodu tutmak | Sadece import satırları |
| 3 | **Public arayüzü tanımlamak** (re-export) | `fetch_top_tracks` + 3 exception |
| 4 | `__all__` ile o arayüzü **yazılı** hale getirmek | Dört isim |

`__all__` = "bu paketin dışarıya vaat ettiği isimler" listesi. İki işi var: `from paket
import *` yazıldığında ne geleceğini belirler, ve daha önemlisi **okuyan insana** neyin
public neyin iç detay olduğunu söyler.

---

## 4. Re-export ne kazandırıyor — somut

`__init__.py` **boş** olsaydı çağıran taraf şunu yazmak zorundaydı:

```python
from lastfm_etl.extract.api import fetch_top_tracks       # iç dosya adına bağlı
```

Re-export sayesinde şunu yazıyor:

```python
from lastfm_etl.extract import fetch_top_tracks           # sadece katmana bağlı
```

Fark, dosya değiştiği gün ortaya çıkar. `api.py` ileride ikiye bölünse
(`api.py` + `pagination.py`), ilk biçimi kullanan **her çağrı yeri** düzeltilir; ikinci
biçimi kullananlar hiçbir şey fark etmez — sadece `__init__.py`'daki tek satır değişir.

Buna **kapsülleme** denir: paketin dışı, içinin nasıl düzenlendiğini bilmez.

---

## 5. Exception'lar neden burada — asıl soru

> *"Error'lar neden import edilsin ki? Onlar sadece raise'lenmiyor mu?"*

`raise` ve `except` **farklı dosyalarda** olur:

```python
# api.py — RAISE eden taraf. İsim burada tanımlı, import gerekmez.
raise LastfmAPIError(code, message)
```

```python
# main.py — EXCEPT eden taraf. İsmi import etmezse NameError alır.
from lastfm_etl.extract import fetch_top_tracks, LastfmAPIError

try:
    payload = fetch_top_tracks(config)
except LastfmAPIError as exc:
    if exc.code == 26:          # suspended key: pipeline'ı durdur, alarm üret
        raise
    logger.error("permanent API failure: %s", exc)
```

`except` bir **isim** ister. O isim çağıranın dosyasında tanımlı değilse import edilmek
zorundadır. Bu yüzden bir modülün fırlattığı exception'lar, döndürdüğü değerler kadar
arayüzünün parçasıdır.

**Test:** *"Çağıran taraf bu ismi yazmak zorunda kalacak mı?"* Evetse public'tir.

Üç exception'ın üçü de farklı bir soruya cevap veriyor:

| Sınıf | Çağıran bunu ne zaman yakalar |
|---|---|
| `LastfmAPIError` | Kalıcı hata; `exc.code`'a bakıp karar verecekse (26 → dur, 6 → parametreyi düzelt) |
| `LastfmTransientError` | Tenacity'nin denemeleri tükendi; "şimdi olmadı, yarın tekrar" demek istiyorsa |
| `LastfmError` | Ayrım umurunda değil; **tek bir yerde** "extract başarısız" demek istiyorsa |

Üçüncüsü taban sınıfın varlık sebebi: `except LastfmError` yazan biri, ileride dördüncü
bir alt sınıf eklensek bile onu da yakalar. Hiyerarşi, çağıranın **ne kadar detay
istediğini seçmesine** izin verir.

> **Karşılaştırma:** `requests` de aynısını yapar — `requests.RequestException` taban,
> `ConnectionError` ve `Timeout` altında. `except requests.RequestException` yazarsan
> hepsini, `except requests.Timeout` yazarsan sadece birini yakalarsın.

---

## 6. Maliyet — neden her şeyi koymuyoruz

| Maliyet | Açıklama |
|---|---|
| **Import süresi** | `__init__.py`'daki her import, paket import edilir edilmez çalışır. AWS Lambda'da bu süre **cold start**'a (fonksiyonun sıfırdan başlatılması) eklenir ve faturalanır |
| **Circular import** | `extract/__init__.py` `transform`'u, `transform` da `extract`'i import ederse Python yarım yüklenmiş bir modül görür ve `ImportError` fırlatır |
| **Gizli bağımlılık** | Paketi import etmek, ihtiyacın olmayan alt modülleri de yükler |

Kural: `__init__.py`'a **çağıranın gerçekten yazacağı** isimler girer, hepsi değil.
`_request` orada yok — o iç detay, adının altçizgiyle başlaması da bunu söylüyor.

---

## 7. Yanlış anlaşılan noktalar

| Barış önce şöyle sandı | Aslında |
|---|---|
| "Exception'lar sadece raise'lenir, import edilmez" | `raise` eden modül import etmez ama **`except` eden çağıran eder**. Exception'lar arayüzün parçasıdır |
| "`__init__.py` boş bir işaret dosyası" | Paket import edilince **çalışan koddur**. İçine yazılan her satır o anda yürütülür |
| "Klasör varsa paket vardır" | Namespace package olarak öyle, ama arayüz tanımlayacak yer olmaz. Sıradan projede `__init__.py` yazılır |
| "`__all__` sadece `import *` için" | Asıl işi **belgelemek**: hangi isim public, hangisi iç detay |
| "Re-export gereksiz tekrar" | Çağrı yerlerini iç dosya adlarından koparır. Dosya bölündüğünde bedeli sıfır olur |

---

## 8. Kanıt

```bash
uv run python -c "import lastfm_etl.extract as e; print(e.__file__)"
```

Beklenen: yol **`extract\__init__.py`** ile biter — yani `lastfm_etl.extract` adı
`__init__.py`'ı gösterir, klasörü değil.

```bash
uv run python -c "import lastfm_etl.extract as e; print(e.__all__)"
```

Beklenen: dört isim.

```bash
uv run python -c "from lastfm_etl.extract import fetch_top_tracks, LastfmAPIError; print('ok')"
```

`__init__.py` boş olsaydı bu komut `ImportError` verirdi — re-export'un ne yaptığının
doğrudan kanıtı.

**Import maliyetini ölç** (cold start argümanının kanıtı):

```bash
uv run python -X importtime -c "import lastfm_etl.extract" 2>&1 | tail -15
```

Her satır bir modülün mikrosaniye cinsinden yükleme süresini verir. `requests` ve
`tenacity`'nin satırlarını gör: `__init__.py`'a bir import eklemek, o modülün süresini
her cold start'a eklemek demektir.

---

## 9. Bir sonraki turda (bu projede yok)

- `__init__.py` içinde `__version__` tanımlamak ve `importlib.metadata` ile senkron tutmak
- Lazy import (PEP 562, `__getattr__`) — cold start'ı düşürmek için ağır modülleri
  ilk kullanımda yüklemek
- `py.typed` işaret dosyası — paketin type hint'lerini dışarıya açmak

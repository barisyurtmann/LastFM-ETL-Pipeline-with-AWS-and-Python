# 19 — Python dil araçları: hızlı referans ve kanıt komutları

**Adım:** P1.1
**Genel mi:** Evet — `dataclass`, `lru_cache`, `getattr`, comprehension, `__post_init__`
her Python projesinde aynı şekilde çalışır.

> **Satır satır anlatım burada değil.** `config.py`'nin yorumlanmış aynası:
> [`docs/annotated/src/lastfm_etl/config.py`](../annotated/src/lastfm_etl/config.py)
> Tasarım gerekçeleri (fail-fast, sır sızıntısı, araç seçimi):
> [`docs/notes/18`](18-config-secrets-and-fail-fast.md)

Bu dosya üç şey tutar: (1) hızlı referans tablosu, (2) iddiaları **çalıştırarak**
doğrulayan komutlar, (3) yanlış anlaşılan noktalar.

> **Kısa cevap** — config.py'deki dil yapıları çalışma zamanında gerçekten ne yapıyor?
>
> 1. `Final` çalışma zamanında hiçbir şeyi kilitlemez; type checker yoksa değer sessizce değişir — tüm type hint'ler böyledir.
> 2. Tuple'ı virgül yapar, parantez değil: `len(("X",))` 1, `len(("X"))` 14 döner.
> 3. `lru_cache`'li `load_config()` testte `monkeypatch.setenv` sonrası eski değeri döner; `cache_clear()` çağrılmalı.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

---

## 1. Hızlı referans

| Sözdizimi | Bir cümlede |
|---|---|
| `Final[X]` | Type checker'a "yeniden atama yok" der; **çalışma zamanında etkisiz** |
| `tuple[str, ...]` | Değişken uzunlukta, hepsi `str`. `...` = `Ellipsis`, "uzunluk serbest" |
| `("a",)` | Tuple'ı **virgül** yapar, parantez değil. `("a")` sadece bir string'tir |
| `@dataclass(frozen=True)` | Atama `FrozenInstanceError`; `eq=True` ile birlikte sınıf hashable olur |
| `slots=True` | `__dict__` yok → yanlış alan adına atama `AttributeError` verir |
| `repr=False` | Dataclass `__repr__` üretmesin; elle yazılan geçerli olsun |
| `__post_init__` | `__init__`'in **sonunda** otomatik çağrılır; doğrulamanın yeri |
| `fields(obj)` | Alan **tanımlarını** döndürür (`.name`, `.type`), değerlerini değil |
| `getattr(obj, "x")` | `obj.x` — ama özniteliğin adı çalışma zamanında string olduğunda |
| `lru_cache` | Sonucu argümanlara göre saklar; testte `f.cache_clear()` şart |
| `find_dotenv()` | Bulamazsa **boş string** döndürür, exception fırlatmaz |
| `load_dotenv(override=False)` | Gerçek ortam değişkeni dosyayı **yener** |
| `logger.debug("%s", x)` | Tembel formatlama + log gruplama; f-string kullanma (`ruff G004`) |
| Bitişik string literal | Derleme anında birleşir, `+` gerekmez |
| `if x:` (boş liste/string) | Boş olan her şey falsy; `len(x) > 0` gürültüdür |

---

## 2. Kanıt komutları

Okumak değil, koşturmak. Her komut yukarıdaki bir satırı doğrular veya çürütür.

```bash
# A — lru_cache aynı nesneyi mi döndürüyor? beklenen: True
uv run python -c "from lastfm_etl.config import load_config as l; print(l() is l())"

# B — frozen gerçekten kilitliyor mu? beklenen: FrozenInstanceError
uv run python -c "from lastfm_etl.config import load_config; c=load_config(); c.lastfm_api_key='x'"

# C — slots typo'yu yakalıyor mu? beklenen: AttributeError ('lastfm_api_ky')
uv run python -c "from lastfm_etl.config import load_config; load_config().lastfm_api_ky='x'"

# D — Final çalışma zamanında koruyor mu? beklenen: HAYIR, sessizce değişir
uv run python -c "
from lastfm_etl import config
config.REQUIRED_ENV_VARS = ('X',); print(config.REQUIRED_ENV_VARS)"

# E — tuple mı string mi? beklenen: 1 ve 14
uv run python -c "print(len(('X',)), len(('X')))"

# F — fields() ne döndürüyor? beklenen: (ad, tip) çifti — değer değil
uv run python -c "
from dataclasses import fields
from lastfm_etl.config import Config
print([(f.name, f.type) for f in fields(Config)])"

# G — __str__ tanımlı değilken str() nereye düşüyor? beklenen: maskeli repr
uv run python -c "from lastfm_etl.config import load_config; print(str(load_config()))"
```

---

## 3. Yanlış anlaşılan noktalar

**Barış önce şöyle sandı:** `Final` değeri kilitler; değiştirmeye kalkarsan hata verir.
**Aslında:** `Final` bir kilit değil, bir **sözleşmedir**. Denetleyecek bir type checker
(mypy/Pyright) kurmadıysan hiçbir koruma yoktur — D komutu bunu gösterir. Aynı şey bütün
type hint'ler için geçerli: `-> None` yazan bir fonksiyon `str` döndürebilir, Python susar.

**Barış önce şöyle sandı:** `__post_init__` `config.py`'de yok, eklenmesi gerekiyor.
**Aslında:** 31. satırda duruyor ve `ee978af` commit'inde onu kendisi yazmıştı. Ders,
Python'la ilgili değil: **dosyanın kendisine bakmadan eksik ilan etme.** `git log -1 --
<dosya>` ve `grep -n "def "` iki saniyelik komutlar.

**Yorum nereye yazılır:** "ne yaptığını" anlatan yorum kodu tekrar eder ve kod
değiştiğinde sessizce yalan söyler. Kodun içindeki yorum yalnızca koda bakarak
**çıkarılamayacak** olanı — gerekçeyi — anlatır. Ders yorumlarının yeri
`docs/annotated/`; oradaki kopya, `#:` işareti sayesinde makineyle doğrulanabilir.

**`W292` — dosya sonunda newline.** `config.py` ilk yazıldığında son satırı sonlandırıcı
karakter olmadan bitiyordu. Sonucu: her `git diff` son satırı "değişmiş" gösterir
(`\ No newline at end of file`), `ruff` `W292` uyarısı verir ve satır bazlı çalışan
shell araçları (`wc -l`, `grep`, `diff`) son satırı bazen saymaz. POSIX'te metin
dosyasının **tanımı** "newline ile biten satırlar dizisi"dir.

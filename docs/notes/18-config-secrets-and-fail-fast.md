# 18 — Config yönetimi, sır yönetimi ve fail-fast

**Adım:** P1.1
**Genel mi:** Evet — her Python projesinde aynı problem, aynı çözüm ailesi.

---

## 1. Config nedir, sabit nedir

Ayrım tek soruyla yapılır: **"Bu değer ortamdan ortama değişiyor mu?"**

| Değer | Değişir mi | Nereye yazılır |
|---|---|---|
| `LASTFM_API_KEY` | Evet (dev key ≠ prod key) | Environment / secret store |
| `S3_RAW_BUCKET` | Evet (`...-dev` vs `...-prod`) | Environment |
| `https://ws.audioscrobbler.com/2.0/` | Hayır | Koda sabit |
| `format=json` | Hayır | Koda sabit |
| Timeout (10 sn) | Sınırda — genelde sabit, gerekirse config | Koda sabit, sonra taşınır |

Junior tuzağı: **her şeyi** config'e taşımak. `BASE_URL`'ü `.env`'e koyan bir proje,
`.env` dosyasını 40 satırlık bir "ayarlar sepeti"ne çevirir; kimse hangisinin gerçekten
değiştiğini bilemez. Config, **ortama bağlı olan** şeydir; "değişebilecek olan" değil.

Bu ayrımın adı **12-factor app**'in III. maddesi ("Config"). Gerçek bir doküman:
<https://12factor.net/config>. Testi şudur: *"Kodu bu anda açık kaynak yapsan, hiçbir
şey sızar mı?"* Sızıyorsa o değer config'tir.

---

## 2. Neden ayrı bir `config.py` — `os.environ` doğrudan kullanılırsa ne kaybedilir

Dağınık `os.environ["X"]` kullanımının **dört** somut maliyeti var. "Daha temiz olur"
bir gerekçe değildir; bunlar gerekçedir.

### (1) Hata zamanı: geç ve derinde

```python
def fetch_top_tracks(limit=100):
    print("istek hazırlanıyor...")
    key = os.environ["LASTFM_API_KEY"]   # burada patlar
```

`os.environ[...]` fonksiyon **gövdesinde** olduğu için, değerlendirme zamanı
import anı değil **çağrı anıdır**. Sonuç: eksik key hatası ancak o satıra ulaşıldığında
görünür.

Local'de fark edilmez (hemen çalıştırırsın). Lambda'da fark eder:

| An | Seçenek A (dağınık `os.environ`) | Seçenek B (`load_config()` en başta) |
|---|---|---|
| Deploy | Sessiz, başarılı görünür | Sessiz (deploy config okumaz) |
| Invocation başlangıcı | Sessiz | **`ConfigError` — anında patlar** |
| İstek hazırlanırken | `KeyError` | — |
| Yan etkiler sonrası | S3'e yarım dosya yazılmış olabilir | Hiçbir yan etki yok |

Kritik olan "patlaması" değil, **ne zaman** patladığı. Yan etki (S3'e yazma, dosya
taşıma) başladıktan sonra patlayan program, yarım iş bırakır. Fail-fast'in tanımı budur:
**hata, geri alınması pahalı hiçbir şey yapılmadan önce ortaya çıkmalı.**

### (2) Env var adı bir string — typo'yu kimse yakalamaz

```python
# extract.py
os.environ["LASTFM_API_KEY"]     # doğru
# transform.py
os.environ["LASTM_API_KEY"]      # bir harf eksik
```

`ruff` bunu göremez (geçerli Python). `mypy` göremez (geçerli `str`). Test kapsamı
o satıra girmiyorsa test de göremez. Hata prod'da, gece, `KeyError` olarak çıkar.

Config modülünde ad **tek yerde** yazılır; kullanım tarafı `config.lastfm_api_key`
olur. Artık typo bir **attribute** hatasıdır — `mypy` ve IDE derhal yakalar.
String'i attribute'a çevirmek, runtime hatasını statik hataya taşımaktır.

### (3) Test edilemezlik

Seçenek A'da fonksiyonun imzasında key yok; dışarıdan içeri giren tek yol global
`os.environ`. Test etmek için testin **global state'i** değiştirmesi gerekir
(`monkeypatch.setenv`). Bu çalışır ama:

- testler birbirini etkiler (biri env'i kirletirse diğeri düşer)
- paralel test (`pytest -n`) risklidir
- fonksiyonun gerçek bağımlılığı imzada görünmez — okuyan anlamaz

Config bir **nesne** olduğunda test şunu yazabilir: `Config(lastfm_api_key="fake")`.
Global state yok, sıra bağımlılığı yok. Buna **dependency injection** denir ve
gerçek faydası tam olarak budur.

### (4) Tip ve doğrulama yeri yok

`os.environ` her zaman `str` döner. `LASTFM_RATE_LIMIT=5` aslında `int` olmalı,
`DEBUG=true` aslında `bool`. Dağınık kullanımda dönüşüm her çağrı yerinde tekrarlanır
ve er geç biri unutur (`if os.environ["DEBUG"]:` → `"false"` string'i de `True`'dur).

Config modülü, dönüşümün ve doğrulamanın **tek** yeridir.

---

## 3. `.env` gerçekte neyi koruyor — tehdit modeli

> **Barış önce şöyle sandı:** ".env'e koyunca sadece local görebiliyor, internet
> göremiyor."
>
> **Aslında:** `.env`'in koruyucu gücü **`.gitignore`'dan** gelir, dosya adından değil.
> Ve koruduğu tek şey **kazara yayınlamaktır**, okunmak değil.

`.env` şifrelenmemiş düz metindir. `git add -f .env` tek komutta korumayı deler.

| Tehdit | `.env` koruyor mu | Gerçek çözüm |
|---|---|---|
| Public repo tarayan bot | **Evet** | `.gitignore` |
| Ekran paylaşımı / screenshot | Hayır | Dikkat |
| Makinedeki malware | Hayır | Kısa ömürlü credential |
| `print(config)` / traceback | Hayır | Maskeli `__repr__` |
| Loglara düşme | Hayır | Maskeli `__repr__` + log review |
| Ekip arkadaşının makinesi | Hayır | Kişi başına ayrı key |

Doğru cümle: **`.env` bir şifreleme değil, bir sınır çizgisidir** — kaynak kodu
konfigürasyondan ayırır. Sınır, "kod git'e girer, config girmez" sınırıdır.

**Prod'da `.env` yoktur.** Lambda'da değerler function'ın environment variable'ları
olarak gelir; daha ciddi kurulumda AWS Secrets Manager veya SSM Parameter Store.
Fark: bunlar erişim kaydı tutar (kim ne zaman okudu), rotasyon destekler ve
disk üzerinde düz metin bırakmaz.

**Key sızdıysa tek doğru refleks:** dosyayı silmek değil, **key'i iptal edip
yenilemek** (revoke + rotate). Git geçmişinden silmek (`filter-repo`, BFG) ikincil iştir;
push edildiği andan itibaren o key yanmıştır.

---

## 4. Sır sızıntısının en sık yolu: otomatik `__repr__`

```python
@dataclass
class Config:
    lastfm_api_key: str

print(Config(lastfm_api_key="abc123"))
# Config(lastfm_api_key='abc123')   ← sır ekranda ve logda
```

`dataclass` varsayılan olarak **bütün alanları basan** bir `__repr__` üretir. Bu repr
şu yerlerde kendiliğinden çalışır:

- `print(config)` ve `logger.info("config: %s", config)`
- traceback'te local değişkenler (Sentry, `rich`, `pytest --showlocals`)
- debugger ve REPL çıktısı
- `pytest` assertion diff'i

Çözüm: `repr=False` verip elle maskeli bir `__repr__` yazmak.

```python
@dataclass(frozen=True, slots=True, repr=False)
class Config:
    lastfm_api_key: str

    def __repr__(self) -> str:
        # Default dataclass repr prints every field; this one must never leak the key
        return f"Config(lastfm_api_key='***{self.lastfm_api_key[-4:]}')"
```

Son 4 karakteri göstermek yaygın pratiktir (kredi kartı mantığı): hangi key'in yüklü
olduğunu ayırt etmeye yeter, key'i kullanmaya yetmez. Tamamen maskelemek de geçerli;
trade-off "teşhis kolaylığı ↔ sızıntı yüzeyi".

**Sınırı bil:** maskeli repr, `logger.info(config.lastfm_api_key)` yazan birini
durdurmaz. Kaza'yı engeller, kastı engellemez.

`pydantic`'te bunun hazır karşılığı `SecretStr` tipidir — repr'de otomatik `**********`
basar, değere `.get_secret_value()` ile erişilir.

---

## 5. Neden `frozen=True` ve `slots=True`

| Parametre | Ne yapar | Neden burada |
|---|---|---|
| `frozen=True` | Nesne immutable; `config.x = ...` `FrozenInstanceError` verir | Config bir **ölçüm**tür; program ortasında değişmesi bug'dır |
| `slots=True` | `__dict__` yerine sabit slot; yeni attribute eklenemez | `config.lastfm_api_kye = ...` typo'su sessizce yeni alan yaratamaz |
| `repr=False` | Otomatik repr üretilmez | Yukarıdaki sızıntı |

`slots=True` Python 3.10+, `frozen` ile birlikte kullanılabilir.

---

## 6. Araç seçimi: `dataclass` vs `pydantic-settings` vs dict

| Yaklaşım | Artı | Eksi | Ne zaman |
|---|---|---|---|
| Düz `dict` | Sıfır kod | Tip yok, autocomplete yok, typo runtime'da | Hiçbir zaman |
| `TypedDict` | Statik tip | Runtime doğrulama yok, davranış (repr) eklenemez | Sadece veri şekli tarif ederken |
| **`@dataclass`** (stdlib) | Bağımlılık yok, tip var, davranış eklenebilir | Doğrulama elle yazılır | **Az sayıda alan** — bizim durumumuz |
| `pydantic-settings` | Otomatik tip dönüşümü, doğrulama, `SecretStr`, `.env` desteği dahili | Ağır bağımlılık (Lambda layer boyutu), öğrenme eğrisi | 10+ alan, iç içe config, çok ortamlı |

Bu projede `dataclass` seçildi: tek alan var, Lambda'ya taşınacak (paket boyutu önemli)
ve elle yazılan doğrulama tam olarak öğrenilmek istenen şey. Alan sayısı büyürse
`pydantic-settings`'e geçmek 20 satırlık bir iştir — geri alması ucuz karar, ADR gerekmez.

---

## 7. `python-dotenv` ve öncelik sırası

```python
from dotenv import load_dotenv
load_dotenv()
```

`load_dotenv()` `.env` dosyasını bulur ve içindeki değerleri `os.environ`'a **yazar**.
İki davranışı bilmek gerekir:

| Davranış | Sonuç |
|---|---|
| `override=False` (varsayılan) | Zaten var olan gerçek env var **ezilmez** |
| `.env` bulunamazsa | Sessizce `False` döner, hata vermez |

Bu ikisi birlikte tam olarak istediğimiz davranışı verir:

```
gerçek environment variable  >  .env dosyası  >  (yok → fail-fast)
```

Lambda'da `.env` dosyası yoktur → `load_dotenv()` no-op olur → değer Lambda'nın
env var'ından gelir. **Aynı kod iki ortamda da doğru çalışır**, `if IS_LAMBDA` gibi
bir dallanma gerekmez. Bu, kütüphanenin kazara değil kasıtlı tasarımıdır.

**Nerede çağrılmalı — tartışmalı konu.** Saf yaklaşım: `load_dotenv()` sadece
uygulamanın giriş noktasında (`__main__`) çağrılır; kütüphane kodu dosya sistemine
dokunmaz. Pratik yaklaşım: `config.load_config()` içinde bir kez çağrılır. Bu projede
ikincisi seçildi çünkü giriş noktası ileride Lambda handler olacak ve orada `.env`
zaten yok; maliyeti sıfır. Bilinçli bir sapmadır, saflık değil.

**Boş değer tuzağı:** `LASTFM_API_KEY=` satırı, key'i `os.environ`'a **boş string**
olarak koyar. `os.environ["LASTFM_API_KEY"]` `KeyError` **vermez** — `""` döner.
Bu yüzden kontrol `if not value.strip()` olmalı, `if name not in os.environ` değil.
"Var mı" ile "dolu mu" farklı sorulardır.

---

## 8. Fail-fast nasıl yazılır: bütün eksikleri topla, bir kere patla

Yanlış:

```python
if not api_key:
    raise ConfigError("LASTFM_API_KEY missing")
if not bucket:
    raise ConfigError("S3_RAW_BUCKET missing")
```

Kullanıcı key'i doldurur, çalıştırır, bu sefer bucket hatası alır, onu doldurur,
üçüncü hatayı alır. Buna **error whack-a-mole** denir.

Doğru: eksikleri bir listede topla, sonunda **tek** hata mesajıyla hepsini bildir ve
mesaja **ne yapılacağını** yaz:

```
ConfigError: Missing or empty environment variables: LASTFM_API_KEY, S3_RAW_BUCKET.
Copy .env.example to .env and fill them in.
```

İyi hata mesajının üç parçası: **ne oldu** · **hangi değer** · **ne yapmalı**.

Ayrıca hata **exception** ile bildirilir, `sys.exit()` veya `print` ile değil:
kütüphane kodu programı sonlandırmaz, karar veren üst katmandır. İşlenmemiş exception
Python'da otomatik olarak exit code `1` üretir — bu da "sessizce başarılı görünme"
problemini çözer.

---

## 9. `lru_cache` ile önbellekleme ve tuzağı

```python
@lru_cache(maxsize=1)
def load_config() -> Config:
    ...
```

Fayda: `load_config()` on yerde çağrılsa da `.env` bir kez okunur, doğrulama bir kez
yapılır ve **her çağrı aynı nesneyi** döner (tutarlılık).

Tuzak: testte `monkeypatch.setenv` ile env'i değiştirirsen cache eski değeri döndürür.
Çözüm testte `load_config.cache_clear()`. Bunu bilmeyen "testim neden eski değeri
görüyor" diye yarım saat kaybeder.

---

## 10. Prod'da ne kırılır

| Senaryo | Belirti | Önleyen şey |
|---|---|---|
| Lambda env var eklenmemiş | Invocation ortasında `KeyError`, yarım S3 yazımı | Handler'ın ilk satırında `load_config()` |
| `.env`'de key var ama boş | `KeyError` yok, API `error 10` döner, anlaşılmaz | `.strip()` boşluk kontrolü |
| Key loglara düştü, CloudWatch 30 gün saklıyor | Sessiz — kimse fark etmez | Maskeli `__repr__` |
| Key rotate edildi, eski değer cache'te | Restart'a kadar 403 | Kısa yaşamlı process / cache_clear |
| İki modülde env var adı farklı yazılmış | Bir yol çalışır, diğeri patlar | Tek config modülü |

---

## 11. Mülakat cevabı

> **"Uygulamanda sırları nasıl yönetiyorsun?"**
>
> "Config'i koddan ayırıyorum — 12-factor'ın III. maddesi. Değerler environment'tan
> gelir; local'de `.env` dosyası bunu doldurur, `.gitignore`'da olduğu için repoya
> girmez, prod'da ise Lambda env var'ı ya da Secrets Manager kullanılır. Aynı kod
> ikisinde de çalışır çünkü `python-dotenv` gerçek env var'ı ezmez.
>
> Okuma tek bir `config` modülünde toplanır ve **uygulama başlangıcında** çağrılır —
> böylece eksik config, yan etki üretilmeden önce patlar. Bütün eksikleri toplayıp
> tek hata mesajında bildiririm; kullanıcı üç kere denemek zorunda kalmasın.
>
> Config nesnesi frozen bir dataclass ve `__repr__`'i maskeli — `dataclass`'ın
> otomatik repr'i bütün alanları basar ve sırlar en sık traceback'ler ve log satırları
> üzerinden sızar. `.env`'in şifreleme olmadığını, sadece kazara yayınlamayı
> engellediğini biliyorum; sızıntı olursa ilk iş dosyayı silmek değil key'i rotate
> etmektir."

---

## 12. Vaka incelemesi: LLM'in ürettiği bir `config.py` neden farklı görünüyor

Referans: eski Spotify ETL denemesinde Gemini'nin ürettiği config dosyası. Çalışıyor,
ama üretim kodu değil. Farklar rastgele değil — her biri bir karara denk geliyor.

### Kritik 1 — sır varsayılan `__repr__` ile sızıyor

`@dataclass` (parametresiz) bütün alanları basan bir repr üretir. `print(config)`
`client_secret`'ı ekrana yazar. Tek satırlık fark: `@dataclass(repr=False)` + elle
maskeli `__repr__`. Bkz. §4.

### Kritik 2 — sınıf seviyesinde varsayılan = import anında donan değer

```python
@dataclass
class SpotifyConfig:
    client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")   # import anında okunur
```

Varsayılan ifadeler **sınıf tanımlanırken bir kez** değerlendirilir, her nesne
oluşturmada değil. Sonuçları:

| Sonuç | Neden önemli |
|---|---|
| Değer import anında donar | `monkeypatch.setenv(...)` sonrası `SpotifyConfig()` hâlâ **eski** değeri döner → test edilemez |
| Sır bir **sınıf attribute'u** olur | `SpotifyConfig.client_secret` nesne oluşturmadan okunabilir; `__dataclass_fields__` ve `help()` çıktısında görünür |
| Doğruluk sıralamaya bağlı | Yalnızca `load_dotenv()` sınıftan **önce** ve **aynı modülde** çağrıldığı için çalışıyor. Import sırası değişirse sessizce boşa düşer |

Doğrusu: okuma bir **fonksiyonun içinde** yapılır (`load_config()`), böylece
değerlendirme zamanı çağrı anıdır.

### Kritik 3 — import yan etkileri

Modül gövdesindeki `print(...)`, `logger.info(...)` ve `load_dotenv(...)` satırları
**import edildiği anda** çalışır. `import config` yapan herkes — `pytest` collection,
bir CLI'ın `--help`'i, dokümantasyon aracı — o çıktıyı üretir.

Kural: **modül import edilmek, iş yapmak değildir.** Modül gövdesinde tanım olur
(fonksiyon, sınıf, sabit); iş fonksiyon çağrısıyla başlar. Aynı sebeple modül sonundaki
`config = SpotifyConfig()` satırı (dosyada yorumlanmış) yanlıştır: env eksikse modül
**import edilemez** hale gelir ve `pytest` daha ilk toplama adımında çöker.

### Kritik 4 — `from src.pipeline.utils.logger import ...`

`src` bir paket değil, bir **layout klasörüdür** (bkz. not 04). `src.` ile başlayan
import yalnızca çalışma dizini proje kökü olduğunda çalışır; kurulu pakette, Lambda'da
veya başka bir dizinden çalıştırıldığında `ModuleNotFoundError` verir. Doğrusu
`from lastfm_etl.utils.logger import get_logger`.

### Orta seviye farklar

| Konu | LLM versiyonu | Üretim pratiği | Sebep |
|---|---|---|---|
| Hata tipi | `ValueError` | Özel `ConfigError` | `except ValueError` alakasız hataları da yutar |
| Hata mesajı | "kimlik bilgileri eksik" | Eksik değişkenlerin **adı** + ne yapılacağı | Hangisinin eksik olduğu belli değil |
| Mesaj dili | Türkçe | İngilizce | Portfolyo repo'su; hata mesajı koddur |
| Mutability | Değiştirilebilir | `frozen=True` | Config çalışma ortasında değişmemeli |
| Attribute koruması | Yok | `slots=True` | Typo yeni alan yaratmasın |
| Boşluk | `os.getenv(x, "")` | `.strip()` eklenir | `"  "` boş sayılmalı |
| Log formatı | `logger.info(f"...")` | `logger.info("... %s", value)` | Aşağıda |

**`%s` vs f-string logging:** f-string, log satırı **atılacak olsa bile** hemen
formatlanır (`logger.debug` kapalıyken bile string üretilir). `%s` ile parametre
geçersen formatlama yalnızca kayıt gerçekten yazılacaksa yapılır. İkinci fayda: log
toplama araçları (CloudWatch Insights, Datadog) aynı **şablonu** paylaşan satırları
gruplayabilir; f-string'de her satır benzersiz olduğu için gruplanamaz. `ruff`'ta
kuralın adı `G004`.

### LLM versiyonunun doğru yaptıkları

Dürüst olmak gerekirse üç şey iyi:

1. **`__post_init__` içinde doğrulama** idiomatik ve bir yönden bizimkinden **güçlü**:
   doğrulama tipin kendisine gömülü olduğu için `SpotifyConfig(client_id="")` de
   yakalanır. Bizim versiyonda doğrulama `load_config()` içinde; `Config(lastfm_api_key="")`
   elle oluşturulursa kontrolden geçmez. Trade-off: doğrulamayı tipe koyarsan test
   double'ları da doğrulamaya uymak zorundadır. İki yaklaşım da savunulabilir.
2. **`find_dotenv()` sonucunu loglamak** — "hangi `.env` yüklendi" sorusu gerçek bir
   teşhis sorusudur, iki makinede çalışırken işe yarar.
3. **Varsayılan `""` verip tipi `str` tutmak** — `str | None` yapıp her kullanımda
   `None` kontrolü yazmaktan iyidir. Gerekçesi doğru.

### Çıkarılacak genel ders

LLM çıktısı **mutlu yolu** yazar: değer okunur, eksikse patlar, iş biter. Üretim kodunu
ayıran şey mutlu yol değil; sızıntı yüzeyi, test edilebilirlik, import semantiği ve
hata mesajının kalitesidir. Bunlar "ekstra özen" değil, kodun asıl işidir — ve bir
LLM'e sormadığın sürece kendiliğinden gelmez.

---

## 13. Logger ne zaman kurulur — config'ten önce mi sonra mı

Sezgi "config bir şey loglayacaksa önce logger modülü yazalım" der. Yanlış sonuç.
Sebep, stdlib `logging`'in iki ayrı işi ayırmasıdır:

| İş | Nerede | Ne gerektirir |
|---|---|---|
| **Logger almak** — `logging.getLogger(__name__)` | Her modülün en üstü | **Hiçbir şey** |
| **Logging'i kurmak** — handler, format, seviye | Sadece uygulamanın giriş noktası, bir kez | Config, çalışan program |

`logging.getLogger(__name__)` bir isim hiyerarşisinde referans döndürür: dosya açmaz,
ayar okumaz, yan etki üretmez. Handler yoksa mesaj hiçbir yere gitmez ve **hata da
vermez**. Yani her modül, hiçbir altyapı olmadan, ilk günden logger alabilir.

**Kütüphane modülünde `logging.basicConfig()` çağırmak hatadır:** import edildiği anda
global root logger'ı ele geçirir ve seni import eden uygulamanın ayarlarını ezer.
"Modül import edilmek iş yapmak değildir" kuralının logging versiyonu.

### Döngüsel bağımlılık riski

Logging kurulumu **config'e muhtaçtır** (seviye `LOG_LEVEL`'dan, format `APP_ENV`'den
gelir). Config de logger modülüne muhtaç olsaydı döngü kapanırdı:

```
setup_logging()  →  load_config()  →  utils.logger  →  setup_logging()   ✗
```

Doğru sıra — **config her zaman en altta, hiçbir şeye muhtaç değil:**

```
1. load_config()          stdlib logging.getLogger, kurulum yok
2. setup_logging(config)  handler ve seviyeyi config'ten kurar
3. asıl iş
```

### Sonuç: config hatası loglanmaz, fırlatılır

`load_config()` çalışırken logging henüz kurulmamıştır — handler yok, `logger.error(...)`
hiçbir yere yazmaz. Bu yüzden `ConfigError` **fırlatılır**: işlenmemiş exception
stderr'a tam traceback basar ve exit code `1` üretir. Hayatın en erken anındaki hata,
en ilkel kanaldan bildirilir.

### `get_logger()` sarmalayıcısı gerekli mi

Çoğu zaman **hayır** — `logging.getLogger(__name__)`'in üzerine bir şey katmayan
sarmalayıcı, tutorial kaynaklı gereksiz dolaylılıktır. Değer katan haller: `structlog`
ile yapılandırılmış alan bağlama, her satıra `correlation_id` iliştirme, Lambda
`request_id`'sini otomatik eklemek. Bunlar bilinmeden yazılan sarmalayıcı, boş bir
katmandır.

### Lambda tuzağı (P3'te karşımıza çıkacak)

Lambda runtime'ı root logger'a **kendi handler'ını önceden kurar**. Sonuç:
`logging.basicConfig()` sessizce no-op olur (`force=True` gerekir) ve seviyeyi elle
set etmezsen `debug`/`info` satırları CloudWatch'ta hiç görünmez.

---

## 14. Doğrulama nerede durur: yükleyicide mi, tipte mi — ikisinde

İki kontrol aynı şey gibi görünür ama farklı muhataplara konuşur:

| Katman | Sorusu | Muhatap | Mesaj |
|---|---|---|---|
| `load_config()` | "`LASTFM_API_KEY` env var'ı dolu mu?" | **Kullanıcı** | "`.env`'i kopyala ve doldur" |
| `Config.__post_init__` | "Bu nesne geçerli durumda mı?" | **Programcı** | "Config alanları boş olamaz" |

Birincisi ortam kontrolü, ikincisi **tipin değişmezi** (invariant). Normal akışta ikincisi
hiç tetiklenmez — o bir **arka duraktır**: test double'ı, ileride yazılacak bir fabrika
fonksiyonu veya Secrets Manager'dan kurulan bir config, geçersiz durumda doğamaz.

Bunun adı **"make illegal states unrepresentable"**. Faydası şu: elinde bir `Config`
varsa geçerli olduğunu *bilirsin*; kullanan hiçbir yerde `if config.api_key:` yazmazsın.

**Karşı argüman (mülakatta sorulur):** "Bu tekrar değil mi?" Değil — aynı koşul, farklı
muhatap. Bazı ekipler tek katmanla yetinir; maliyeti 4 satır olduğu ve `load_config()`
tek giriş yolu kalmayacağı için iki katman savunulabilir.

**`fields(self)` ile gezmek:** doğrulama alan adını elle yazarak değil, dataclass'ın
alan listesini gezerek yapılır. Yeni alan eklendiğinde doğrulama kendiliğinden kapsar.
Elle yazılan kontrol listesi, alan eklendiğinde güncellenmesi unutulan ilk yerdir.

---

## 15. Bir sonraki turda (bu projede yok)

- Çoklu ortam: `.env.dev` / `.env.prod` seçimi ve `APP_ENV` değişkeni
- AWS Secrets Manager / SSM Parameter Store'dan okuma ve cache'leme
- `detect-secrets` / `gitleaks` pre-commit hook'u — commit anında sır taraması
- `direnv` — dizine girince `.env`'i otomatik yükleyen shell aracı
- `setup_logging()`: dictConfig, JSON formatlayıcı, `LOG_LEVEL` env var'ı (P2.1)
- `structlog` ve yapılandırılmış loglama; CloudWatch Insights sorguları

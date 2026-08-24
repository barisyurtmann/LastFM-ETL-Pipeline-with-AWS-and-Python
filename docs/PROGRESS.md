# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi ve "bitti" tanımları için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-24
**Current step:** P2 — Local extract + transform
([plan](ROADMAP.md#adım-p2--local-extract--transform))
**Next sub-step:** **P2.1 kod tarafı bitti, sayfalama kararı açık.** `_request` ve
`fetch_top_tracks` çalışıyor; mutlu yol ve hata yolu ölçüldü. Kapanmadan önce tek soru
var: sayfalama döngüsü nereye ait? Aşağıda.

### 2026-08-24 — OTURUM (ev makinesi): ortam kurulumu, IAM kullanıcı yeniden adlandırıldı

**Kod yazılmadı — bu bir kurulum oturumu.** P2.1'in açık kararı (sayfalama döngüsü nereye
ait) el değmeden duruyor, aşağıdaki bölümde.

**Ev makinesi durumu:**

| Kontrol | Sonuç |
|---|---|
| `git status` | temiz, `main...origin/main` |
| Python | 3.14.5 — `requires-python = ">=3.14,<3.15"` aralığında |
| `.env` | var, `LASTFM_API_KEY` dolu |
| `.venv` | **bayat bulundu**, `uv sync` gerekiyor — çıktısı bu oturumda doğrulanmadı |
| AWS CLI | `aws-cli/2.36.29` kuruldu, `aws configure` yapıldı, region `eu-central-1` |
| Access key | bu makine için **ayrı** anahtar üretildi (description tag'li). Kullanıcı başına 2 anahtar limitinin ikincisi; üçüncü makine gerekirse doğru cevap 3. anahtar değil, SSO |

`.venv` neden bayattı: 10 Ağustos'ta kurulmuş, içinde yalnızca editable install vardı.
`requests`, `tenacity` ve `python-dotenv` sonradan eklendi (`35f97a2`, `ecd3ac9`).
**`git pull` bağımlılık getirmez** — `.venv/` gitignore'lu, gelen şey yalnızca `uv.lock`.
Runbook 00'ın `git pull → uv sync` sırası tam bu yüzden var; atlanırsa hata
`ModuleNotFoundError` olarak, bağımlılığın eklenmesinden günler sonra çıkar.

**IAM kullanıcı yeniden adlandırıldı: `lastfm_etl_dev` → `lastfm-etl-dev`.**

Sapma 22 Ağustos'taki P1.2 oturumunda doğmuş: üç doküman (runbook 00, runbook 03, not 21)
kullanıcıyı tire ile yazmış, AWS'de duran kaynak alt çizgiliydi. **Doküman değil, kaynak
düzeltildi.** İki sebep: S3 bucket adları alt çizgi kabul etmez, yani projenin geri kalanı
zaten tire; ve maliyet bugün ~0 — ARN'e referans veren policy yok (`AdministratorAccess`
AWS-managed). P3.4'te rol trust policy'leri yazıldıktan sonra aynı işlem elle policy
düzeltmesi gerektirirdi.

Yöntem: **bu işlem konsolda yok.** `aws iam update-user --user-name <eski>
--new-user-name <yeni>`. AWS dokümanı açıkça *"There is no option in the console to rename
a user"* diyor. Bu, not 20'deki "konsol API'nin bir istemcisidir" iddiasının somut kanıtı:
konsol her operasyonu göstermek zorunda değil. Junior refleksi "konsolda yoksa yapılamaz"
demek; doğru refleks API referansına bakmak.

Değişen: ARN ve konsola giriş kullanıcı adı. Değişmeyen: `UserId` (`AIDA...`), access
key'ler, MFA cihazı, bağlı policy'ler. Kalıcı kimlik `UserId`, okunabilir kimlik ad —
`surrogate key` / `natural key` ayrımının aynısı, P2.3'te tekrar çıkacak.

Düzeltmenin gerçek gerekçesi kozmetik değil: runbook'un doğrulama adımı *"`Arn`
`user/lastfm-etl-dev` ile bitmeli, bitmiyorsa dur"* diyor. Bırakılsaydı üçüncü bir makinede
**doğru** kurulum "dur" sinyali verirdi. Yanlış alarm veren kontrol, kontrolsüzlükten
kötüdür — insan bir süre sonra o adımı atlamayı öğrenir, ve gerçekten bozulduğu gün de atlar.

**ADR yazılmadı — bilinçli.** ADR kuralı "geri alması pahalı kararlar". Yeniden adlandırma
bugün ucuz ve geri alınabilir; bir isimlendirme sözleşmesi ADR'si de henüz genelleştirecek
kadar veri yok (tek örnek). Karar P3.4'te rol adlarıyla tekrarlanırsa ADR adayı olur.

**Not şablonu genişletildi (`notes/README.md`):** beşinci bölüm — `Mülakat cevabı`.
Format **karar → gerekçe → trade-off**; karar içermeyen saf referans notlarında `—` ile
geçilir. Eski notlara **toplu doldurulmaz**: hatırlanmayan bir kararın gerekçesi yazıldığında
üretilmiş bir cevap olur, hatırlanmış değil. İlk uygulama not 21 §10 — access key vs SSO,
credential chain'in kodu ortamdan bağımsız kılması, makine başına ayrı anahtar.

**Ev makinesinde kapatılmamış tek iş:** `uv sync` + üç doğrulama komutunun çalıştırılması.

---

### 2026-08-24 — OTURUM: P2.1 request yolu çalışıyor

**Yazılan kod:** `src/lastfm_etl/extract/api.py` (151 satır). `_request` beş adımlı
sırayla gövdelendi, `fetch_top_tracks` params + delegasyon.

**Ölçüldü:**

| Yol | Sonuç |
|---|---|
| Mutlu yol, `limit=5` | `@attr` geldi, 5 kayıt |
| Bozuk key | `LastfmAPIError` code 10, **hiç `WARNING` yok** — kalıcı hata retry edilmedi |

İkinci satır, ADR-0014'ün taksonomi iddiasının çalıştığının kanıtı. Retry mekanizması
tenacity'nin, ama "ne zaman" kararı bizim kodumuzda ve doğru davranıyor.

**İskelette bulunan hata — düzeltildi.** 22 Ağustos'ta yazılan TODO, JSON çözülemediğinde
koşulsuz `LastfmError` (kalıcı) fırlatıyordu. Gerçek senaryo: API'nin önündeki gateway 503
döndüğünde gövde HTML olur. O sırayla, retry edilmesi gereken geçici bir arıza kalıcı
sayılır ve tenacity hiç devreye girmezdi. Düzeltme: decode hatasında **önce status'a bak**.
Ders: hata sınıflandırması tek bir sinyale (burada "JSON mu?") dayandırılırsa, o sinyalin
başka sebeplerle de bozulabildiği durumlar sessizce yanlış tarafa düşer.

**Barış'ın ilk denemesi ve neden yanlıştı** (aynada da duruyor):

```python
except (LastfmTransientError):
    raise
```

İki ayrı hata. (1) `session.get()` asla `LastfmTransientError` fırlatmaz — o *bizim
fırlatmak istediğimiz* tip, `requests`'in fırlattığı değil (`requests.RequestException`).
Bu `except` hiçbir zaman tetiklenmez. (2) Çıplak `raise` yakalananı aynen tekrar fırlatır,
yani blok hiçbir iş yapmaz. `try/except`in amacı **tip çevirmektir**: alt katmanın hatası
→ bizim domain hatamız.

**Bu oturumda verilen kararlar:**

| Karar | Gerekçe |
|---|---|
| **Yorum politikası değişti**: `src/` altında az yorum (sadece *neden*), ders tamamen `docs/annotated/` aynasına | Barış: *"orjinal kodda çok not olmasın."* Portfolyo dosyası temiz kalır, öğrenme materyali aynada birikir. `annotated/README.md` sözleşmesi zaten bunu öngörüyordu |
| `TOP_TRACKS_METHOD` sabiti açıldı | Aynı string üç yere gidiyor: request params, log satırı, exception mesajı. Üçünden birindeki yazım hatası **sessiz** olurdu |
| `int(payload["error"])` bir `try` içinde | `RETRYABLE_ERROR_CODES` bir `frozenset[int]`. API bir gün `"29"` (string) dönerse `"29" in {29}` sessizce `False` olur ve retry hiç çalışmaz |
| `raise_for_status()` **kullanılmadı** | Last.fm geçersiz key'e HTTP 200 döner — `raise_for_status` en kritik hatayı hiç görmez. Ayrıca fırlattığı `HTTPError` bizim tipimiz değil, tenacity onu retry etmez |

**Kapatılan ADR borcu:** 0013 (katman bazlı paket yapısı), 0014 (tenacity). İkisi de
"kod çalışınca yazılır" kuralına uyularak, kod ölçüldükten **sonra** yazıldı.

**Yazılan ayna:** `docs/annotated/src/lastfm_etl/extract/api.py` (746 satır). Bölüm 0'da
yedi ön koşul kavram: exception nesnesi ve `raise`, `except`in kalıtımla eşleşmesi,
`try/except/as/from` zinciri, decorator'ın ne olduğu, keyword-only `*`, `frozenset` + `in`
tuzağı, `requests` Session/Response. Sapma kontrolü temiz.

---

### AÇIK KARAR — P2.1 bunsuz kapanmaz: sayfalama döngüsü nereye ait?

`fetch_top_tracks` **tek sayfa** döndürüyor. ADR-0006 ise "hedef sayıya kadar sayfalama"
diyor ve gerekçesi kayıtlı: `limit=100` bugün çalışıyor ama Last.fm `limit`'i kırparsa
cevap **sessizce kısa** gelir, hata fırlamaz.

Yani bir döngü gerekiyor ve henüz hiçbir yerde yok. Üç seçenek:

| Seçenek | Sonuç |
|---|---|
| `extract/api.py` içinde ikinci bir fonksiyon (`fetch_top_tracks_until`) | Sayfalama extract'ın işi sayılır. P2.1'in kapsamı büyür ama ROADMAP P2.1 satırı zaten "top-100 sayfalama" diyor |
| Çağıranda (P2.2, raw yazan kod) | `api.py` saf kalır: tek çağrı = tek istek. Ama sayfalama mantığı raw yazma koduna karışır |
| Hiç döngü yok, `limit=100` tek istek | Ölçüldü ve çalışıyor. ADR-0006'nın gerekçesini **çürütmeden** iptal etmek olur — yapılırsa yeni ADR gerekir |

**Bununla bağlantılı, PROGRESS'te zaten duran kısıt:** raw katman her sayfayı **ayrı** ve
`@attr` ile birlikte saklamak zorunda, aksi halde `rank` kurtarılamaz. Döngü nereye
konursa konsun bu kısıt geçerli.

**ROADMAP itirazı hâlâ karara bağlanmadı:** P2.1 satırındaki "top-100 sayfalama" ifadesi,
yukarıdaki karar verilince ya doğrulanır ya düzeltilir. Karar önce, ROADMAP sonra.

---

### Öğrenme yöntemi — bu oturumda konuşuldu, karara bağlanmadı

Barış: *"kodu %60-70 anlayabiliyorum ama kendim asla yazabilecek gibi değilim."*

Teşhis: **tanıma–üretme açığı** (recognition–recall gap). Okurken anlamak, üretebilmenin
kanıtı değil; akıcı görünen materyal öğrenildiği yanılsaması üretir. LLM ile çalışmak bunu
tarihte hiç olmadığı kadar kolaylaştırıyor.

Ayrım yapılmalı: `wait_exponential_jitter` parametrelerini ezberden yazamamak **normal**
(kimse yazmaz, aranır). "Önce gövdeyi oku, sonra status'a bak" sırasını yazamamak
**normal değil** — o bir karar, sözdizimi değil.

Bedeli üç yerde ödenir: prod'da gece 3'te teşhis, üretilen kodun sessizce yanlış olduğu
anı görebilmek (bu oturumda tam olarak yaşandı — iskeletteki hatayı Barış fark etmedi),
ve mülakatta kendi yazmadığın kodun gerekçesini savunmak.

Önerilen ama **seçilmeyen** yöntem: 3 satırlık versiyondan başlayıp 8 turda büyütmek
(her turda 3-5 yeni satır, her tur tek bir sorunu ekliyor). Barış "böyle devam edelim"
dedi. Kabul edilen şart: **aynadaki KANIT komutları terminalde çalıştırılacak.**
Çalıştırılmayan açıklama okunmuş sayılmaz.

Bir sonraki alt adımda tekrar değerlendirilecek. Aday ara basamak: boşluklu iskelet
(*faded worked example*) — ben imzayı ve yorumları veririm, gövdedeki isimleri Barış
doldurur.


### 2026-08-22 — OTURUM SONU (iş makinesi): P2.1 iskeleti hazır, gövdeler evde

**Devam noktası: `extract/api.py` içindeki iki `TODO(barış)`.**

| Fonksiyon | Durum |
|---|---|
| `_request` | İmza + docstring + tenacity decorator hazır. **Gövde yok** — beş adımlık TODO içeride |
| `fetch_top_tracks` | İmza + docstring hazır. **Gövde yok** — params sözlüğü + delegasyon |

Evde sırayla: `git pull` → `uv sync` → `_request` → çalıştır → `fetch_top_tracks` → çalıştır.
Doğrulama komutları TODO'ların altında; mutlu yol **ve** bozuk key ile hata yolu ölçülecek.
Bozuk key'de **hiç `WARNING` satırı olmamalı** — retry denenmemeli.

**Bu oturumda verilen kararlar:**

| Karar | Gerekçe |
|---|---|
| **Karma mod** (`PROJECT_CONTEXT.md` §1d) | §1c'nin "Claude yazar" kuralı fazla genişti. Barış: *"tüm kodu sen yazarsan anlamayabilirim, ama her şeyi de ben yazamam."* Claude iskelet (imza, type hint, docstring, sabit, exception hiyerarşisi), Barış gövde |
| **Katman klasörleri açıldı**: `extract/`, sonra `transform/` (P2.3), `load/` (P2.2) | 0.3'te "gerçek payload görülünce kararlaşacak" diye ertelenmişti. Payload görüldü, şema kararlaştı, ROADMAP'te iki katman daha kesin — artık tahmin değil plan |
| `utils/`, `main.py`, `Makefile`, `Dockerfile`, CI **açılmadı** | İhtiyaç doğmadan yazılan yardımcı, hiç silinmeyen ölü koddur. `setup_logging()` ve `main.py` P2.4'te doğacak; geri kalanı ROADMAP → Sonraki tur |
| Dosya adı `extract/api.py` (`lastfm.py` değil) | Paket zaten `lastfm_etl`; `lastfm_etl.extract.lastfm` kendini tekrar ediyor. Kaynak **türüne** göre adlandırma (`api.py`, ileride `s3.py`) daha genişleyebilir |
| **tenacity** ile retry, elle döngü değil | Barış: *"kolayı varken zorlaştırmak mantıksız."* Kabul. Ama sınırı yazılı: tenacity retry'ın **nasıl**'ını çözer, **ne zaman**'ını çözmez — `RETRYABLE_ERROR_CODES` taksonomisi ve "gövdeyi status'tan önce oku" sırası aynen duruyor. Tenacity'nin sildiği ~20 satır: elle backoff + retry döngüsü |
| `reraise=True` | Yoksa tenacity son hatayı `RetryError` içine sarar ve çağıran, karar vermek için gereken Last.fm error kodunu kaybeder |
| `26` (suspended key) **retryable değil** | Askıya alınmış anahtarı tekrar denemek durumu kötüleştirir |

**ROADMAP'e itiraz — karara bağlanmadı:** P2.1 satırı "top-100 sayfalama" diyor ama 1.8'de
ölçüldü: `limit=100` tek istekte geliyor (`perPage=100`, tek sayfa). İskelet buna göre
yazıldı — döngü yok, `page` parametresi imzada duruyor. **ROADMAP P2.1 satırı düzeltilmeli.**

**Yazılan not:** `docs/notes/22-packages-init-and-public-api.md` — `__init__.py`'nin dört
işi, re-export ve kapsülleme, `__all__`, cold start maliyeti. Tetikleyen soru:
*"error'lar neden import edilsin ki, onlar sadece raise'lenmiyor mu?"* Cevap: `raise` eden
modül import etmez, **`except` eden çağıran eder** — exception'lar arayüzün parçasıdır.

**ADR borcu — kod çalışınca yazılacak, önce değil:**

| ADR | Konu |
|---|---|
| 0013 | Katman bazlı paket yapısı (`extract/`, `transform/`, `load/`) |
| 0014 | Retry için tenacity bağımlılığı |

Sebep `adr/README.md`'nin kendi kuralı: *"An ADR is written after the code that justifies
it works."* Bu repoda ADR-0007 ve 0008 bu kurala uyulmadığı için yazıldı ve tek satır kod
çalışmadan supersede edildi.

**Ayna borcu:** `docs/annotated/` içine `extract/api.py` ve `extract/__init__.py` aynaları
**gövdeler bitince** yazılacak. Yarım kodun aynası yanlış bilgi taşır.

> **ADIM 0 TAMAMLANDI.** **ADIM 1 TAMAMLANDI** (1.1–1.8). **P1 TAMAMLANDI** (P1.1–P1.3).
> **Adım A–E (dlt/dbt) hiç başlanmadı ve iptal edildi** (ADR-0009).
> **İLK PYTHON KODU YAZILDI** — `src/lastfm_etl/config.py`, 63 satır. `src/` artık 0 değil.
> **P2'DEN İTİBAREN her oturumun çıktısı `src/` altında çalışan koddur.**

### 2026-08-22 — P1.3 KAPANDI, P1 BİTTİ: iki bucket ayakta

İki bucket konsoldan oluşturuldu, `aws s3api` ile doğrulandı: bölge `eu-central-1`,
versioning `Enabled`, dört public access bloğu `true`, `Project=lastfm-etl` tag'i.

**Kararlar ve doküman borcunun kapanışı:**

| Doküman | Karar |
|---|---|
| **ADR-0011** | Her kaynak `eu-central-1`'de. Bucket bölgesi değişmez; Glue/Athena/Lambda aynı bölgede olmak zorunda |
| **ADR-0012** | İki bucket (raw + transformed), kursun tek bucket + prefix'i yerine. Belirleyici gerekçe: transform Lambda'nın kendi çıktısıyla tetiklenmesi **yapısal olarak** imkânsız hale geliyor |
| **runbook 04** | Bucket oluşturma prosedürü, isimlendirme kuralları, key şeması, geri alma |

**Key şeması kararlaştırıldı, oluşturulmadı** (S3'te klasör yoktur; kod yazdığı anda ağaç
görünür):

```
lastfm-etl-raw-<ek>/          to_processed/lastfm_raw_<ISO8601-UTC>.json
                              processed/lastfm_raw_<ISO8601-UTC>.json
lastfm-etl-transformed-<ek>/  tracks/  artists/
```

Zaman damgası **ISO 8601 basic + UTC** (`20260822T030000Z`): alfabetik sıra = kronolojik
sıra, ve S3 listelemesi alfabetiktir.

**Bucket adındaki `raw/` tekrarı kaldırıldı.** ROADMAP P2.2 key şemasını
`raw/to_processed/...` diye yazıyordu — bucket adı zaten `...-raw-...` olduğu için bu
tekrardı (tek-bucket varsayımından kalma). ADR-0012 ve runbook 04 `to_processed/` kullanıyor.
**ROADMAP.md P2.2 satırı buna göre düzeltilmeli** — açık iş.

### 2026-08-22 — P1.2 KAPANDI: AWS CLI kuruldu, kimlik doğrulandı (iş makinesi)

Access key **yeniden üretildi** — ev makinesinde 20 Ağustos'ta üretilen anahtarın secret'ı
elde değildi. Secret yalnızca üretim ekranında görünür; o ekran kapandıysa anahtar ölüdür.

| Adım | İş | Durum |
|---|---|---|
| 5A | IAM → `lastfm-etl-dev` → yeni access key, tag `cli-otomasyon-laptop` | ✔ |
| 5B | `winget install --id Amazon.AWSCLI -e`, terminal kapat-aç | ✔ |
| 5C | `aws configure` → key, secret, `eu-central-1`, `json` | ✔ |
| 5D | `aws sts get-caller-identity` → `Arn` `user/lastfm-etl-dev` ile bitiyor | ✔ |

**Bu oturumda öğrenilen/karara bağlanan:**

| Konu | Sonuç |
|---|---|
| Tek anahtar birden çok makinede kullanılır mı | Teknik olarak evet. Ayırmak **tercih**: blast radius, CloudTrail attribution, rotation kolaylığı. IAM limiti kullanıcı başına 2 anahtar → ev + iş tam sınırda. 3. makine gerekirse doğru cevap 3. anahtar değil, SSO |
| Description tag | Kozmetik değil: tag'siz anahtar teşhis edilemez → silinemez → bilinmeyen aktif anahtar olarak kalır |
| `aws configure` sırası | 5B'nin 5A'dan **önce** yapılması daha doğru — secret'ın ekranda/CSV'de bekleme süresini kısaltır. Bu turda 5A önce yapıldı, CSV `aws configure` sonrası silindi |
| AWS anahtarı `.env`'e **girmiyor** | `.env` projenin sözleşmesi, AWS kimliği makinenin kimliği. Ayrıca `.env`'e koysak kodun onu okuması gerekirdi ve P3'te Lambda rolü zinciri kırılırdı |

**Yazılan notlar** (mentor kural ihlali sonrası: `boto3` tanımlanmadan üç mesaj kullanıldı):

- `docs/notes/20-aws-sdk-and-boto3.md` — AWS bir API'dir, `boto3` ne yapıyor, SigV4,
  `client` vs `resource`
- `docs/notes/21-aws-credentials-and-the-credential-chain.md` — IAM kavramları, access key
  kuralları, `~/.aws` iki dosya ayrımı, credential chain, güvenlik listesi

İkisi de `notes/README.md`'deki ~60 satır şablonunu aşıyor (~100 satır). Bilinçli: ikisi de
sıfırdan kavram kuruyor, hatırlatma tablosu değil. Şablonun "ikiye böl" tavsiyesi uygulandı.

**YENİ DOKÜMAN KATEGORİSİ: `docs/runbooks/`** (2026-08-22)

Barış'ın tespiti: *"Ben 2 ay sonra baktığımda bugün yaptığım işlemleri bu notlara bakıp
tekrar yapamam."* Doğru — ve eksik olan bir not değil, bir **kategori**ydi. `notes/` bir
işin *ne* ve *neden*'ini tutuyor, *nasıl*'ını değil. Konsolda yapılan hiçbir şeyin
(hesap açma, MFA, budget, IAM kullanıcı, access key) tekrarlanabilir kaydı yoktu.

İlk turda yalnız AWS runbook'u yazıldı ve `01` numarası verildi. Barış itiraz etti:
*"ortadan başlamışız gibi olmuş"* — haklıydı, projenin ilk 35 commit'i runbook'suzdu.
Aynı oturumda geriye dönük olarak tamamlandı ve numaralandırma kronolojik hale getirildi.

| Dosya | İçerik |
|---|---|
| `runbooks/README.md` | Kategori tanımı, `notes` ↔ `adr` ↔ `runbook` ayrım testi, şablon, numaralandırma politikası |
| `runbooks/00-new-machine-setup.md` | **Yeni makine:** `git clone` → `uv sync` → `.env` → AWS kimliği → beş doğrulama + günlük akış |
| `runbooks/01-repo-scaffold.md` | **Adım 0:** `git init` → `.gitignore` (+ `check-ignore` doğrulaması) → `.gitattributes` + CRLF normalizasyon dizisi → `pyproject.toml` + `src/` layout → `uv sync` → `.env.example` + README |
| `runbooks/02-lastfm-api-access.md` | **Adım 1:** key alma → `set -a; source .env` → ilk çağrı → **dört hata deneyi** → sayfalama/`@attr` → fixture kaydetme → rate limit |
| `runbooks/03-aws-account-bootstrap.md` | **P1.2:** hesap → root MFA → budget → IAM kullanıcı → kullanıcı MFA → access key → CLI → `aws configure` → doğrulama → temizlik (**eski `01`, yeniden numaralandırıldı**) |

Her runbook'ta: bitiş durumu, bölüm başına doğrulama, sorun giderme tablosu, geri alma
bölümü, **son doğrulama tarihi** (UI ve komutlar eskir).

**Dürüstlük işareti:** `01` ve `02` geriye dönük yazıldı. Ölçüm sonuçları PROGRESS'te
kayıtlıydı ama bazı komutların birebir metni değildi — o satırlar runbook'ta **⚠ ile
işaretlendi**: "aynı sonucu üretir, o gün yazılan satırın kopyası değildir". Uydurulmuş
bir komutun doğrulanmış gibi durması, hiç yazmamaktan kötüdür.

AWS konsol adımları resmî dokümana karşı doğrulandı (IAM user, sanal MFA, budget şablonu).

`PROJECT_CONTEXT.md` §8 doküman tablosu güncellendi: `runbooks/` eklendi, tabloda eksik
olan `annotated/` de eklendi, `notes/` ↔ `runbooks/` ayrım testi yazıldı.

**Kalan runbook borcu:** `04` — S3 bucket oluşturma, P1.3 bitince.

**Bekleyen doküman borcu — P1.3 bitince yazılacak iki ADR:**

| ADR | Karar | Neden ADR (geri alması pahalı) |
|---|---|---|
| **0011** | Bölge: `eu-central-1` | Bucket'ın bölgesi sonradan değişmez; veriyi taşımak gerçek iş |
| **0012** | **İki bucket** (`raw` + `transformed`), kursun tek bucket + iki prefix'i yerine | Bucket adı küresel benzersiz ve yeniden adlandırılamaz; sonradan birleştirmek/ayırmak veri taşıma demek |

**Bucket topolojisi tartışması (2026-08-22, ADR-0012'nin ham gerekçesi):**
Kurs tek bucket açıp altına `raw/` ve `transformed/` klasörü koyuyor. İkisi de meşru.
İki bucket'ın kazancı: (1) transform Lambda'nın kendi çıktısıyla tetiklenip sonsuz döngüye
girmesi **yapısal olarak** imkânsız hale gelir — tek bucket'ta bunu yalnızca event filtresi
önler ve filtre unutulabilir; (2) versioning/lifecycle/encryption/bucket policy **bucket
seviyesinde** ayarlanır, prefix seviyesinde değil — raw ile transformed'ın farklı politikaya
ihtiyacı var; (3) IAM'de kaynak sınırı `bucket/*` yazmak, prefix deseni yazmaktan daha az
hata götürür. Maliyet farkı yok, bucket ücretsiz. Bu bir mühendislik tercihi, yayınlanmış
bir standart değil.

> **Düzeltme (2026-08-22, aynı oturum):** Claude karşı argüman olarak "hesap başına bucket
> limiti 100" demişti. **Yanlış** — AWS varsayılan kotayı 10.000'e çıkardı. Yani "bucket
> pahalı bir kaynaktır, prefix'le idare et" argümanı çöktü; iki bucket lehine olan denge
> daha da güçlendi. Kalan tek karşı argüman: her yeni bucket adı **küresel** namespace'te
> bir çakışma riski, ve silinen bir bucket adı hemen (hatta hiç) geri gelmeyebilir.

### 2026-08-20 — OTURUM SONU: nerede kaldık, evde nereden devam

**Devam noktası: P1.2, adım 5B.** Tarayıcı tarafı bitti (5A dahil), terminal tarafı
başlamadı. Evde ilk iş `git pull`.

**P1.2 kontrol listesi** — hangi adımın bittiğini işaretleyerek ilerle:

| Adım | Nerede | İş | Durum |
|---|---|---|---|
| 1 | Tarayıcı | AWS hesabı | ✔ |
| 2 | Tarayıcı | Root kullanıcıya MFA | ✔ |
| 3 | Tarayıcı | Budget alarm, aylık 5 USD, e-posta uyarısı | ✔ |
| 4 | Tarayıcı | IAM kullanıcı `lastfm-etl-dev` + `AdministratorAccess` + MFA | ✔ |
| 5A | Tarayıcı | Access key üretildi (CLI use case) | ✔ |
| **5B** | **Git Bash** | **`winget install --id Amazon.AWSCLI -e`, pencereyi kapat-aç** | **← buradan devam** |
| 5C | Git Bash | `aws configure` → key, secret, `eu-central-1`, `json` |  |
| 5D | Git Bash | `aws sts get-caller-identity` → Arn'de `user/lastfm-etl-dev` |  |
| P1.3 | Tarayıcı | İki bucket, konsoldan tıklayarak |  |

> **Secret access key yalnızca üretildiği ekranda görünür.** O sayfa kapandıysa
> anahtar kaybolmuştur — IAM'den eskisini sil, yenisini üret. Panik yok, ücretsiz.

**Bu oturumda verilen kararlar:**

| Karar | Gerekçe |
|---|---|
| **Öğrenme konsoldan yapılacak**, CLI'dan değil | Barış'ın tercihi: S3/Lambda/CloudWatch/Glue/Athena arayüzünü görmek istiyor. Konsol ile CLI aynı API'ye gider, biri diğerini gizlemez |
| CLI yine de kurulacak | Sebep öğrenme değil: `boto3` kimlik doğrulamak için `~/.aws/credentials` dosyasını okuyor ve o dosyayı `aws configure` yazıyor. P2.2'de kod S3'e bu sayede yazacak |
| AWS CLI `winget` ile, `uv` ile değil | `uv` Python kütüphanesi kurar (`.venv` içine, projeye özel); `winget` Windows uygulaması kurar (sisteme). AWS CLI kodun bağımlılığı değil, elin aleti. Ayrıca CLI v2 PyPI'da yayınlanmıyor — `pip install awscli` eski v1'i kurar |
| Bölge: **`eu-central-1`** (Frankfurt) | İstanbul'a en yakın, Lambda/Glue/Athena hepsi mevcut. Bucket oluşturulduktan sonra bölgesi **değişmez** |
| Bucket adları: `lastfm-etl-raw-<ek>`, `lastfm-etl-transformed-<ek>` | S3 bucket adları küresel olarak benzersiz; sonek çakışmayı önlüyor |
| İnsan kullanıcıya `AdministratorAccess` | Least privilege **makine kimliklerine** uygulanacak (Lambda rolleri, P3.4). Tek kişilik öğrenme hesabında insanı kısmak her adımda `AccessDenied` demek. Bu bir mühendislik tercihi, yayınlanmış bir standart değil |
| Bucket'larda versioning **açık** | S3'te silme geri alınamaz; versioning açıkken silinen nesne "delete marker" alır, orijinali durur |

**Bekleyen doküman borcu:** bucket'lar oluşturulduktan sonra **ADR-0011 — bölge seçimi**
yazılacak. Gerekçe: bucket'ın bölgesi sonradan değişmiyor, veriyi taşımak gerçek iş —
yani geri alması pahalı bir karar, ADR tanımına giriyor. Şimdi yazılmıyor çünkü karar
henüz uygulanmadı.

### 2026-08-20 — P1.1 KAPANDI: config.py ölçüldü, beş kontrol de geçti

`src/lastfm_etl.config` ilk kez çalıştırıldı (Python 3.14.3, Git Bash, ev makinesi).

| # | Ölçülen | Sonuç |
|---|---|---|
| 1 | `print(load_config())` | `Config(lastfm_api_key='***f29d')` — `.env` okundu, repr maskeli |
| 2 | `LASTFM_API_KEY=` ile çağrı | `ConfigError: Missing or empty environment variables: LASTFM_API_KEY...`, `echo $?` → **1** |
| 3 | `Config(lastfm_api_key='   ')` | `ConfigError: Config fields must not be empty: lastfm_api_key` — `__post_init__` arka durağı çalışıyor |
| 4 | `basicConfig(DEBUG)` + `load_config()` | İki DEBUG satırı; ikincisi maskeli config |
| 5 | `git status --short` | `.env` **listede yok** |

KONTROL 2 önemli bir şeyi kanıtladı: `.env` diskte dolu olduğu hâlde hata alındı. Sebep
`load_dotenv(override=False)` — gerçek ortam değişkeni dosyayı yener. Üretimde (.env'in
olmadığı Lambda'da) doğru davranış budur ve artık ölçülmüş durumda.

**P1.1 kapanış işleri (aynı commit):**

| İş | Durum |
|---|---|
| `.env.example` Türkçe yorumlar → İngilizce | Yapıldı. "2.5'teki fail-fast" ifadesi "P1.1" olarak düzeltildi, dosya sonu newline eklendi |
| `requires-python` çelişkisi | Çözüldü → `>=3.14,<3.15` |
| `PROJECT_CONTEXT` §2 "Python 3.12+" | `3.14` olarak güncellendi |

**Python 3.14 ↔ Lambda uyumu konusu KAPANDI.** AWS Lambda `python3.14` runtime'ını
Kasım 2025'te yayınladı; `.venv`'in 3.14.3 olması artık bir risk değil, **hedefle
eşleşme**. Üst sınır (`<3.15`) bilinçli: `pandas`/`pyarrow` gibi derlenmiş wheel'ler
minor sürüme bağlıdır, 3.15'te kurulan bir layer 3.14 runtime'ında `ImportError` verir.
(Ağustos 2026 itibarıyla Lambda'da Python 3.15 yalnızca public preview.)

### 2026-08-20 — ÇALIŞMA MODU DEĞİŞTİ: hız modu

Karar `PROJECT_CONTEXT.md` §1c'de. Özet:

| Konu | Yeni kural |
|---|---|
| `src/` altını kim yazar | **Claude yazar, Barış review eder ve çalıştırır** |
| Tahmin soruları | **Sorulmaz.** Doğrudan anlatılır |
| Rota | ROADMAP sırası **bozulmuyor**: P1.1 → P1.2 → P1.3 → P2 |
| Değişmeyen | Kodu Barış çalıştırır, commit'i Barış atar, her `.py` aynasıyla birlikte gelir |

Sebep: 35+ commit, ~10.000 satır doküman, 63 satır kod — ve o kod hiç çalıştırılmadı.
Doküman kalitesi sorun değildi; darboğaz yazma hızı ve mesaj başına ilerlemeydi.

**Claude projesinin instructions alanı da elle güncellenmeli** — repo dosyası Claude'un
davranışını değiştirmez, yeni oturum eski kurala döner.

### Bu oturumda (2026-08-20, ev) yapılanlar — kod yok, ayna yeniden yazıldı

**Sorun:** ayna okunduğu hâlde anlaşılmıyordu. Sebep teşhis edildi: "kod bloğu başına
en fazla 3 satır yorum" bütçesi yalnızca **neden**e yer bırakıyor, **ne olduğu**na
bırakmıyordu. `Final çalışma zamanında kilitlemez, mypy'ye söyler` cümlesi; type hint,
type checker, mypy ve çalışma zamanı kavramlarının bilindiğini varsayıyor. Bilinmiyorsa
cümle bilgi taşımıyor. Aynı hata not 19'da da vardı: o bir **hatırlatma tablosu**,
öğrenme metni değil — ama ilk öğrenme için kullanılıyordu.

**Bilinmeyenler ölçüldü** (25 maddelik listeden işaretlenenler): `Final`/köşeli parantezli
tipler, mypy, `@dataclass`ın ürettiği kod, `frozen`/`slots`/`repr`, class-instance-`self`,
dunder metotlar, kalıtım, `raise`/exception, docstring, `getattr`, `fields()`, ortam
değişkeni, logging, `.strip()`/`join()`, modül seviyesi kod ve import anı.
**Bilinenler:** type hint sözdizimi, tuple/list, decorator, comprehension'lar, f-string,
`%s` logging, slicing, truthy/falsy, `__name__`.

| Ne | Durum |
|---|---|
| `docs/annotated/src/lastfm_etl/config.py` | **Yeniden yazıldı: 107 → ~550 satır.** Satır bütçesi kaldırıldı |
| — yeni **Bölüm 0** | Aşağıdaki her şeyin ön koşulu olan 6 kavram (modül/import anı, class-instance-`self`, dunder, kalıtım, exception/`raise`, docstring) dosyanın başında, satır aralarına serpiştirilmeden |
| — yeni yazım sözleşmesi | Her açıklama **NE → KANIT → BİZDE** sırasını izler; her iddianın çalıştırılabilir bir kanıt komutu var |
| `docs/annotated/README.md` | Yeni sözleşme yazıldı; `notes/` ile sınır değişti: eskiden "özel bilgi / genel bilgi", artık **öğretme / hatırlatma**. Çelişkide **ayna kaynaktır** |
| `docs/notes/19-...` | KONTROL C düzeltildi + iki "önce şöyle sandım" maddesi eklendi + başına "bu not öğretmez, hatırlatır" uyarısı |
| `src/lastfm_etl/config.py` | **Dokunulmadı.** Sapma kontrolü temiz |

**İki ölçüm, iki yanlış doküman iddiası düzeltildi** (hem Python 3.11 hem 3.14'te koşuldu):

| İddia | Gerçek |
|---|---|
| `slots` typo'da `AttributeError` verir | `frozen` + `slots` birlikteyken **`TypeError`**. Sebep: `frozen`ın ürettiği `__setattr__` kapanışta slots'suz eski sınıfı tutar, `type(self) is cls` yanlış çıkar. Yalnız `slots` olsaydı `AttributeError` olurdu |
| `repr=False` olmasa üretilen repr elle yazılanı ezerdi | **Ezmez** — dataclass sınıfta tanımlı `__repr__`in üstüne yazmaz. `repr=False`'ın işi hata modunu güvenli yapmak: elle yazılan silinirse `<Config object at 0x...>` çıkar, anahtar değil |

İkisi de "mantıken böyle olmalı" ile "çalıştırdım, şu çıktı" farkının örneği.

**Sıradaki iş değişmedi:** P1.1'in 5 KONTROL komutu hâlâ çalıştırılmadı.

### Bu oturumda (2026-08-19) yapılanlar — kod yok, doküman altyapısı

**Yeni doküman kategorisi: `docs/annotated/`.** `src/` altındaki her `.py` dosyasının
satır satır Türkçe yorumlanmış **aynası** burada durur. Yol `src/`'in birebir aynasıdır:
`docs/annotated/src/lastfm_etl/config.py` ↔ `src/lastfm_etl/config.py`.

Gerekçe: düz metin not (18, 19) kodu okurken açıklamayı **başka dosyada** aratıyor.
Açıklamanın kodun yanında olması gerekiyor, ama kodun içinde olamaz — repo portfolyo,
kod İngilizce ve kodun içindeki yorum "neden"i anlatır, "ne yaptığını" değil.

**Kopya sapması nasıl çözüldü:** aynada `#:` ile başlayan her satır açıklamadır ve
gerçek dosyada yoktur; kalan her karakter birebir aynıdır. Sapma makineyle ölçülür:

```bash
grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/config.py | diff - src/lastfm_etl/config.py
```

Çıktı boşsa ayna güncel. Kural: **ayna, kaynağıyla aynı commit'te güncellenir.**
Bundan sonra yazılacak her `.py` için aynası da yazılacak.

| Ne | Durum |
|---|---|
| `docs/annotated/README.md` | Klasörün kuralı, `#:` sözleşmesi, sapma kontrolü, borçlar |
| `docs/annotated/src/lastfm_etl/config.py` | 107 satır; `config.py`'nin 63 satırı + kod bloğu başına max 3 satır yorum |
| `docs/notes/19-...` | Yeniden yazıldı: satır satır anlatım aynaya taşındı, notta hızlı referans + 7 kanıt komutu + yanlış anlaşılan noktalar kaldı |
| `docs/notes/README.md` | 19 eklendi + `annotated/` bölümü |
| `src/lastfm_etl/config.py` | **Tek karakter değişti:** dosya sonuna newline (`ruff W292`) |

**`__post_init__` zaten vardı.** Bu oturumda "eksik" sanıldı; 31. satırda duruyor ve
`ee978af` commit'inde yazılmıştı. Ders not 19 §3'te.

**`config.py`'ye başka hiçbir şey eklenmedi — bilinçli.** "Production config'lerinde
olup burada olmayanlar" listesi ve her birinin **hangi adımda** geleceği aynanın
sonundaki blokta yazılı (APP_ENV, LOG_LEVEL, timeout, AWS_REGION, secret store,
pydantic-settings). Bugün eklemek, hiçbir kod dalının okumadığı alanlar üretirdi.

**Ölçülen yan bulgu:** `git ls-files --eol` → `i/lf w/crlf`. `.gitattributes` yalnızca
**checkout** anında satır sonu çevirir; Windows'ta editörle *yeni yaratılan* dosya
worktree'de CRLF kalır, index'e LF girer. Zararsız ama 03 numaralı notun "w/lf" iddiası
yeni dosyalar için geçerli değil.

### Bu oturumda (2026-08-17, iş makinesi) yapılanlar

| Ne | Durum |
|---|---|
| `uv add python-dotenv` | `pyproject.toml` `dependencies` doldu, `uv.lock` gerçek içerik kazandı |
| `src/lastfm_etl/config.py` | Yazıldı — `Config` (frozen dataclass) + `ConfigError` + `load_config()` |
| `docs/notes/18-config-secrets-and-fail-fast.md` | Yazıldı (15 bölüm) |
| `docs/notes/README.md` | Index'e 18 eklendi |
| KONTROL 1–5 | **Çalıştırılmadı.** Evde ilk iş |

**`config.py`'de verilen kararlar** (gerekçeleri not 18'de):

| Karar | Sebep |
|---|---|
| `@dataclass(frozen=True, slots=True, repr=False)` | Immutable + typo koruması + otomatik repr'in sır sızdırmasını engelleme |
| Elle maskeli `__repr__` | Sır en sık traceback/log üzerinden sızar, `print(config)`'ten değil |
| `__post_init__` + `fields(self)` gezme | Tipin değişmezi; arka durak. Yeni alan otomatik kapsanır |
| `load_config()` içinde okuma (sınıf gövdesinde değil) | Sınıf seviyesi varsayılan import anında donar → test edilemez |
| `@lru_cache(maxsize=1)` | Tek okuma, tutarlı nesne. **Testte `load_config.cache_clear()` gerekecek** |
| `logging.getLogger(__name__)`, `basicConfig` yok | Kütüphane logger *alır*, uygulama logging'i *kurar*. `setup_logging()` P2.1'de |
| `logger.debug("... %s", x)` (f-string değil) | Lazy formatlama + log gruplama (`ruff G004`) |
| Hata loglanmıyor, fırlatılıyor | `load_config()` çalışırken logging henüz kurulmamıştır |

### Evde ilk iş (ev makinesi)

1. `git pull`
2. **`.env` kontrolü:** ev makinesinde `LASTFM_API_KEY` **0 byte'tı**. İş makinesinde 32
   karakter. `.env` git'e girmediği için ev makinesine **gelmeyecek** — key'i elle
   doldur, yoksa KONTROL 1 patlar (ki bu doğru davranıştır).
3. Aşağıdaki 5 kontrolü sırayla çalıştır.

**P1.1 — KONTROL komutları (Git Bash):**

```bash
# 1 — mutlu yol + maskeleme → beklenen: Config(lastfm_api_key='***XXXX')
uv run python -c "from lastfm_etl.config import load_config; print(load_config())"

# 2 — fail-fast + exit code → beklenen: ConfigError ve echo $? = 1
LASTFM_API_KEY= uv run python -c "from lastfm_etl.config import load_config; load_config()"
echo $?

# 3 — __post_init__ arka durağı → beklenen: ConfigError: Config fields must not be empty
uv run python -c "from lastfm_etl.config import Config; Config(lastfm_api_key='   ')"

# 4 — logger: kurulumsuz sessiz, kurulunca iki DEBUG satırı (config maskeli)
uv run python -c "
import logging; logging.basicConfig(level=logging.DEBUG)
from lastfm_etl.config import load_config; load_config()
"

# 5 — sır git'e sızmıyor → .env listede OLMAMALI
git status --short
```

> PowerShell kullanıyorsan KONTROL 2 farklı: `$env:X=""` değişkeni **siler**, boş
> bırakmaz. Onun yerine `.env`'i geçici olarak `.env.bak` yap, komutu çalıştır, geri al.
> Exit code'u `$LASTEXITCODE` ile oku.

**Beşi de geçtiğinde P1.1 kapanır.** Kapanış işleri (sırayla):

1. `.env.example`'daki Türkçe yorumları İngilizce'ye çevir + "2.5'teki fail-fast"
   ifadesini düzelt (aşağıda açık iş 1)
2. `requires-python` kararı (açık iş 2 + aşağıdaki Python 3.14 uyarısı)
3. Commit → `PROGRESS.md` güncelle → **P1.2'ye geç** (AWS IAM kullanıcı + budget alarm)

### ~~Yeni açık konu: Python 3.14 ↔ Lambda runtime uyumu~~ — KAPANDI 2026-08-20

> Aşağıdaki bölüm tarihsel kayıt olarak duruyor. Endişe geçersiz çıktı: Lambda
> `python3.14` runtime'ını Kasım 2025'te yayınladı. Karar: `requires-python = ">=3.14,<3.15"`.



`.venv` **Python 3.14** ile kurulmuş (`__pycache__` dosyaları `cpython-314`). AWS
Lambda'nın desteklediği en yeni runtime bundan geride. Şu an bir şey kırmıyor çünkü
`python-dotenv` saf Python. **P2'de `pandas` ve `pyarrow` girdiğinde kıracak:** bu
kütüphanelerin derlenmiş wheel'leri Python sürümüne bağlıdır ve 3.14 için kurulan bir
Lambda layer'ı 3.13 runtime'ında `ImportError` verir.

→ **P3.1'e girmeden önce** venv'i Lambda runtime'ıyla aynı sürüme çekmek gerekecek
(`uv python pin`). Karar P1.1 kapanışında `requires-python` ile birlikte verilecek.

**Açık işler:**

| # | İş | Durum |
|---|---|---|
| 1 | `.env.example` içinde **Türkçe yorumlar** var | **Kapatıldı** (2026-08-20). İngilizce'ye çevrildi, "2.5" → "P1.1", dosya sonu newline eklendi |
| 2 | `pyproject.toml` `requires-python = ">=3.11"` | **Kapatıldı** (2026-08-20). `>=3.14,<3.15` — Lambda `python3.14` runtime'ı ile eşlendi |
| 3 | `PROJECT_CONTEXT.md` mimari + araç düzeltmesi | **Yapıldı.** §4 kursun mimarisiyle eşlendi, §2 saf Python'a döndü |
| 4 | Repo adı `LastFM-ETL-...` | **Değişmiyor.** Mimari yeniden ETL (ADR-0009); isim doğru |
| 5 | Rate limit çelişkisi (`5/dakika` vs `5/saniye`) | **Düzeltildi.** Doğrusu **saniyede ~5**. `PROJECT_CONTEXT.md` §3 yanlıştı, not 17 doğruydu |
| 6 | ADR-0009 başlığı (`Retire dlt and dbt` önerisi) | **Kapatıldı.** Olduğu gibi kalıyor; başlık tartışması kapsam şişmesidir |
| 7 | `PROGRESS.md` "Tamamlananlar" geçmişi | Budanmadı, **budanmayacak.** 9 günün kanıtı orada |

**Kurulu olanlar:** `python-dotenv` (P1.1'de eklendi).
**Kurulu olmayanlar:** `requests`, `pandas`, `pyarrow`, `boto3` — hepsi P2'de gelir.

---

## ROADMAP REVİZYONU — 2026-08-15 (üçüncü ve son): plan kursun kendisinden türetildi

Aynı gün üçüncü revizyon. İlk ikisi (9 adımlık elle plan, sonra A–E dlt/dbt planı) hiç
uygulanmadan iptal edildi.

**Ölçüm — bütün revizyonların tek gerekçesi:**

| | Değer |
|---|---|
| Süre | 2026-08-07 → 2026-08-15 (9 gün) |
| Commit | 31 |
| `docs/` | 9.527 satır |
| `src/` + `tests/` Python kodu | **0 satır** |

**Teşhis:** planlar kaynağı olmadan yazılıyordu. Kapsamın dış bir çıpası olmadığı için
hiçbir şey "kapsam dışı" olamıyordu; her bileşen bir tasarım tartışmasına dönüşüyordu.

**Bu revizyonun farkı:** plan artık **kursun dört parçasından** türetildi. Kapsam
sorusunun mekanik bir cevabı var — kursta yoksa ve "structure" listesinde yoksa,
sonraki tur. Gerekçe: ADR-0010.

| | İlk plan | A–E (dlt/dbt) | **Şimdi (P1–P4)** |
|---|---|---|---|
| Kaynak | yok | yok | **kursun 4 parçası** |
| Adım | 9 | 5 | **4** |
| Alt adım | ~50 | 39 | **14** |
| Yeni araç | — | dlt, dbt, DuckDB | **yok** |
| Mimari | ETL | ELT | **ETL** (kurs) |

**Kurstan dört bilinçli sapma** (gerekçeler ADR-0010'da):

| Konu | Kurs | Burada | Sebep |
|---|---|---|---|
| API | Spotify (OAuth) | **Last.fm** (`api_key`) | Adım 1 Last.fm'i ölçtü, key ve fixture'lar hazır |
| Kütüphane | `spotipy` | **`requests`** | Last.fm'in wrapper'ı yok; wrapper hata yolunu gizler |
| Tablo | 3 (albums, artists, songs) | **2** (tracks, artists) | `chart.getTopTracks` album döndürmüyor. JOIN dersi duruyor |
| Format | CSV | **Parquet** | Crawler CSV'de tipi tahmin eder; Parquet tipi taşır |

**Doküman kuralı:** not artık **koddan sonra** yazılıyor ve hiçbir adımı bloklamıyor.
Uzunluk sınırı yok. Gerekçe: ADR-0007 sıfır kod varken yazıldı ve aynı gün supersede
edildi. Uygulanmamış bilgiyi dondurmak, yanlış bilgiyi dondurmaktır.

Eski numaralar (`0–9`, `A–E`) **yeniden kullanılmadı**. Eşleme `ROADMAP.md`'de.

---

## Tamamlananlar

- [x] **0.1** `.gitignore` yazıldı ve `git check-ignore -v` ile doğrulandı.
      Kritik kontrol: `src/lastfm_etl/raw` **eşleşmedi** — kalıplar yeterince dar yazılmış.
- [x] **0.2** İlk commit atıldı: `chore: add .gitignore`
- [x] `docs/` yapısı kuruldu (PROGRESS, ADR, notes) — `docs: add project documentation structure`
      ADR-0001 yazıldı, `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı,
      custom instructions yenilendi.
- [x] **CRLF/LF normalizasyonu** (ROADMAP'te yazmayan, araya giren iş).
      `.gitattributes` ile `* text=auto eol=lf` — `chore: enforce LF line endings via .gitattributes`
      Semptom: içerik değişmeden `1127 insertions / 1127 deletions`. Sebep: iş
      makinesi tüm docs'u CRLF ile yeniden yazmıştı.
      `git ls-files --eol` ile `i/lf w/lf` doğrulandı. Not: `docs/notes/03-line-endings.md`
- [x] **0.3** `pyproject.toml` + `src/` layout.
      Paket adı kararı: dağıtım `lastfm-etl`, import `lastfm_etl`. Önceki
      `src/lastfm-pipeline/` klasörü silindi — tire içeren isim `SyntaxError` verir,
      import edilemez. Boş alt klasörler (`extract/`, `transform/`, `load/`, `utils/`)
      açılmadı: modül yapısı Adım 1'de gerçek payload görüldükten sonra kararlaşacak.
      ADR-0002 yazıldı. Notlar: 04, 05, 06.
      **Uyarı:** kurulabilirlik doğrulanmadı — venv 0.4'te geliyor.
- [x] **`.gitignore` düzeltmesi** (ROADMAP'te yazmayan, araya giren iş).
      `.gitignore` **satır sonu yorumu desteklemez** — sadece `#` ile *başlayan* satır
      yorumdur. `__pycache__/`, `*.py[cod]`, `*.egg-info/` ve `.venv/` pattern'ları
      yorum metnini de içerdiği için **hiçbir şeyle eşleşmiyordu**.
      `fix: correct .gitignore patterns broken by inline comments`
      0.1'deki doğrulama `.env` ve `data/` üzerinden yapıldığı için (o satırlarda inline
      yorum yok) fark edilmemişti. Ders: doğrulama **örnek** üzerinden değil, **her
      pattern** üzerinden yapılır. Not: `docs/notes/01`.
- [x] **0.4 kararı:** `uv`, project mode. ADR-0003 yazıldı.
      Gerekçe özeti: 8.6 zaten lock dosyası istiyor; `uv` onu, dev/prod ayrımını ve
      Python sürüm yönetimini tek araçta veriyor. "Önce venv+pip, sonra uv" alternatifi
      reddedildi — üç araç öğrenmek demek olurdu ve `uv` zaten `.venv/`/`pyvenv.cfg`/
      `PATH` mekanizmasını gizlemiyor. Notlar: 07, 08.
- [x] **0.4** Sanal ortam kuruldu. `uv` 0.12.2 (winget), `uv sync` → `.venv/` + `uv.lock`.
      **PROGRESS ile ADR-0003 çelişkisi düzeltildi:** buradaki eski sıra
      `uv venv` → `uv pip install -e .` idi; bu **pip mode**'dur ve `uv.lock`'a bakmaz,
      yani ADR'de reddedilen modelin komutlarıydı. Project mode'da doğru komut tek:
      `uv sync`. Not: 09.
      **0.3'ün devredilmiş doğrulaması geçti** —
      `uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"` çıktısı
      `src\lastfm_etl\__init__.py`, `site-packages` altı değil. Editable install çalışıyor,
      0.3 artık gerçekten kapalı.
      `git status` temiz kaldı: `.venv/` ignore'lu, sadece `uv.lock` yeni dosya olarak çıktı.
- [x] **0.5** `.env.example` + `README.md`.
      `.env.example` şimdilik tek anahtar (`LASTFM_API_KEY`, değeri boş). `LASTFM_USER`
      gibi adaylar bilinçli olarak eklenmedi — config mi CLI argümanı mı olacağı 2.1'in
      konusu. **Devredilen doğrulama:** `.env.example` ile gerçek `.env` arasındaki
      anahtar senkronu 1.1'de (gerçek key alınınca) doğrulanacak.
      README altı bölüm: özet, status, prerequisites, setup, structure, docs haritası.
      Usage/badge/mimari şeması bilinçli olarak **yok** — çalışan komut yokken yazmak
      "aspirational README" olurdu. 8.8'de eklenecek. Not: 10.
- [x] **`check-ignore` tuzağı** (araya giren iş). `git check-ignore -v .env.example`
      exit `0` döndürdü ve dosya ignore'luymuş gibi göründü — oysa değildi.
      Sebep: `-v` bayrağı exit code'un anlamını değiştiriyor ("ignore'lu" değil,
      "bir pattern ile eşleşti" — negation dahil). Doğrulama `git status` /
      `git add --dry-run` ile yapılır. Not 01'e Tuzak 3 olarak eklendi.
- [x] **0.6 — ADIM 0 KAPANDI.** Bitti tanımının beş maddesi:

      | Madde | Nasıl doğrulandı |
      |---|---|
      | `git status` temiz, türev dosya yok | `.venv/`, `*.egg-info/`, `uv.lock` sonrası temiz |
      | `.env` ve `data/` gerçekten ignore'lu | `git check-ignore` + `git status` (boş `.env` ile) |
      | Paket temiz ortamda kurulup import edilebiliyor | `uv run python -c "import lastfm_etl"` → `src/` yolu |
      | `.env.example` var, gerçek `.env` yok | Doğrulandı; **anahtar senkronu 1.1'e devredildi** |
      | README bir yabancıya yetiyor | Boş klasörde `git clone` + README'yi sıfırdan takip — geçti |

- [x] **İş makinesi ortamı kuruldu** (ROADMAP'te yazmayan, araya giren iş).
      `winget install --id=astral-sh.uv -e` → terminal kapat-aç → `uv sync`.
      Doğrulama geçti: `import lastfm_etl` çıktısı `src\lastfm_etl\__init__.py`,
      `git status` temiz. İki makine artık aynı `uv.lock`'tan besleniyor.
- [x] **1.1** Last.fm API key alındı, `.env`'e yazıldı.
      **Shared Secret bilinçli olarak eklenmedi.** Gerekçe: bu proje yalnızca public
      chart metodlarını (`chart.getTopArtists` vb.) çağırıyor; bunlar sadece `api_key`
      ister. `shared_secret` yalnızca `api_sig` üretmek için gerekir — yani authenticated
      metodlarda (`track.scrobble`, kullanıcıya özel veri). Kullanılmayan bir sır sıfır
      fayda sağlar ama sızma yüzeyini büyütür; ayrıca `.env.example`'a eklenirse sözleşme
      yalan söyler.
      Ayrım: `api_key` **kim olduğunu** söyler, `shared_secret` **o olduğunu kanıtlar**.
      **0.5'ten devredilen doğrulama kapandı:** `git status` gerçek sır içeren `.env`'i
      göstermiyor, `git status --ignored --short` `!! .env` diyor, `.env.example` ile
      anahtar seti birebir aynı (tek anahtar: `LASTFM_API_KEY`).
- [x] **1.2** API elle çağrıldı (`curl.exe`), `format=json` ile ve olmadan.
      **Ölçüm — tuzak gözle doğrulandı:**

      | | `format` yok | `format=json` |
      |---|---|---|
      | Status | `200` | `200` |
      | `Content-Type` | `text/xml` | `application/json` |
      | Gövde ilk karakteri | `<` | `{` |

      Kritik sonuç: **iki cevabın status kodu aynı.** `raise_for_status()` bu durumu
      yakalayamaz; ayrım yalnızca `Content-Type` header'ında ve gövdede görünür.
      Sır komut geçmişine sokulmadı — `.env` önce oturuma yüklendi, URL'de
      `$env:LASTFM_API_KEY` kullanıldı. Metod seçimi keyfi değil: `PROJECT_CONTEXT.md` §4
      zaten `method=chart_gettopartists` yolunu varsayıyor.
      Not: `docs/notes/11`.

- [x] **1.3** Bozuk `api_key` ile çağrıldı. **Ölçüm, beklentiyi çürüttü.**

      | Deney | Status | Content-Type | Gövde |
      |---|---|---|---|
      | Bozuk `api_key` | `403` | `application/json` | `{"message":"Invalid API key...","error":10}` |
      | Bozuk `method` | `400` | `application/json` | `{"message":"Invalid Method...","error":3}` |

      Beklenti `200` + gövdede hata idi (`PROJECT_CONTEXT.md` §3'ün eski hâli ve
      Claude'un iddiası). Gerçek: Last.fm HTTP status kodlarını **doğru** kullanıyor.
      `Content-Type: application/json` ve gövde formatı, cevabın araya giren bir
      WAF/CDN'den değil Last.fm'in kendisinden geldiğini kanıtlıyor.
      `PROJECT_CONTEXT.md` §3 ölçüme göre düzeltildi.
      **Ders:** iddia, kod yazılmadan önce ölçüldüğü için ucuza düzeltildi. Adım 1'in
      var oluş sebebi tam olarak bu.
      **Gövde kontrolü yine de zorunlu, ama gerekçesi değişti** — "HTTP yalan söylüyor"
      değil, "HTTP yeterince şey söylemiyor": `403` tek başına `error 10` (geçersiz key)
      ile `error 26` (askıya alınmış key) arasını ayırt edemez, retry sınıfını belirleyemez,
      ve `raise_for_status()` fırladığı anda gövde okunmadan akış kopar.
      **Yan bulgu:** `requests`, `HTTPError` mesajına **tam URL'yi** gömüyor — query
      string dahil. Gerçek key kullanılsaydı traceback'te düz metin olarak dururdu.
      Not 11 §8.2'deki teorik risk canlı kanıtla doğrulandı. Maskeleme 3.7'de.
      **ADR adayı düzeltmesi:** ROADMAP'te 3.3 için yazan
      *"Treat HTTP 200 with an error body as a failure"* başlığı ölçüme uymuyor;
      ADR yazılırken *"Validate both HTTP status and response body"* olacak.

- [x] **METOD DEĞİŞİKLİĞİ (1.4'te alındı):** ilk dilim `chart.getTopArtists` yerine
      **`chart.getTopTracks`** ile yapılacak. Gerekçe satır sayısı **değil** (o `limit`
      parametresine bağlı), **şema derinliği**: `getTopTracks` iç içe `artist` nesnesi,
      `duration` gibi sayısal alan ve `streamable`'ın metoda göre farklı tip alması gibi
      gerçek dönüşüm problemleri taşıyor. `getTopArtists` düz bir tablo — transform katmanı
      tek satıra inerdi ve 5.4 (düzleştirme) öğrenilmeden geçilirdi.
      `PROJECT_CONTEXT.md` §3 ve §4 buna göre güncellendi.
- [x] **1.4** Üç payload `tests/fixtures/lastfm/` altına kaydedildi:
      `chart_gettoptracks_success.json` (31 KB, 20 parça), `error_10_invalid_api_key.json`,
      `error_3_invalid_method.json`. ADR-0004 yazıldı.
      **Konum kararı:** `docs/samples/` değil `tests/fixtures/`. Gerekçe: *doğrulanan
      kaynak kazanır* — test kodu dosyayı gerçekten okur, yol değişirse test kırılır.
      Dokümanı çalıştıran bir şey yok, orada dosya silinse kimse fark etmez. Doküman
      payload'ı **kopyalamaz, link verir**; iki kopya kaçınılmaz olarak sapar.
      **Biçim kararı:** pretty-printed (`json.tool --no-ensure-ascii`). Ana gerekçe
      okunabilirlik değil **git diff**: tek satırlık JSON'da alan değişikliği görünmez.
      `--no-ensure-ascii` olmadan non-ASCII karakterler `\uXXXX` kaçışlarına dönüşürdü.
      **Bu kural raw katmanın tam tersi** (4. adım byte düzeyinde sadakat istiyor) —
      aynı veri, farklı amaç, farklı kural. Karıştırılırsa 4.1'in tuzağına düşülür.
      **Güvenlik kontrolü geçti:** `grep -rn "api_key" tests/` → eşleşme yok. Payload
      isteği yankılamıyor. Her yeni fixture'da tekrarlanmalı.
- [x] **Shell bilgisi boşluğu kapatıldı** (araya giren iş). `\`, `|`, `>`, `&&`, `||`,
      `/dev/null`, exit code, `export`/`source`/`set -a` ve kullanılan komutlar
      (`ls`, `mkdir -p`, `grep`, `echo`) not 12'de toplandı. Ayrıca bash ↔ PowerShell
      sözlüğü. Gerekçe: `PROJECT_CONTEXT.md` §7 shell'i "konunun kendisi" sayıyor;
      CI, Dockerfile, cron ve Makefile hep shell.
      **Düzeltme:** verdiğim komutlardaki `set -a` teknik olarak gereksizdi — `$VAR`
      komut satırında geçtiğinde bash onu zaten genişletiyor. Export yalnızca alt süreç
      (`os.environ`) okuyacaksa gerekli. Adım 2'de gerekli olacağı için alışkanlık
      olarak yazıldı.

- [x] **1.5** Payload anatomisi ölçüldü. Not 13 (keşif protokolü) yazıldı.

      **Yapı:** `{"tracks": {"track": [...], "@attr": {...}}}`. Bir kaydın alanları:
      `name, duration, playcount, listeners, mbid, url, streamable, artist, image`.
      `artist` ve `streamable` iç içe nesne, `image` dört elemanlı dizi.

      **XML kökeni her şeyi açıklıyor.** Last.fm JSON üretmiyor — XML üretip çeviriyor.
      Üç sonucu var: (1) **istisnasız her sayı string** (`"duration": "184"`, `@attr`
      içindeki sayfa numaraları dahil), çünkü XML'de tip yok; (2) `#text` anahtarı bir
      veri değil **yapı kalıntısı** — XML'de `<image size="small">url</image>` gibi hem
      öznitelik hem metin taşıyan eleman JSON'a böyle çevrilir; (3) XML'de `null`
      kavramı olmadığı için eksik veri `""` olarak gelir, `None` olarak değil.
      Ölçüldü: payload'da hiç `None` yok.

      **Tek elemanlı liste tuzağı YOK.** `limit=1` ile ölçüldü → `list` döndü, tek dict
      değil. Yani 5. adımda normalizasyon kodu (`if isinstance(t, dict): t = [t]`)
      **yazılmayacak**. Ölçmeseydik "her ihtimale karşı" yazılırdı — §6'nın yasakladığı
      şey. Ölçüm bazen kod eklettirir, bazen kod yazdırmaz.

      **EN ÖNEMLİ BULGU — ilk sayfa yalan söyledi.** Aynı endpoint, aynı gün, tek fark
      `page` numarası:

      | Ölçüm | `page=1` | `page=500` |
      |---|---|---|
      | Kayıt sayısı | 20 | **19** |
      | Boş `mbid` (track) | 0 | **4 (%21)** |
      | Boş `mbid` (artist) | 0 | 1 |
      | `duration == 0` | 0 | **2** |
      | Alan setleri aynı mı | True | **False** |

      Sebep: chart popülerlik sıralı. En popüler kayıtlar en iyi kürate edilmiş olanlar —
      ilk sayfa veri kalitesinin **en yüksek** olduğu yer. Adı: **seçim yanlılığı**.

      **`mbid` bazen boş değil, anahtar olarak HİÇ YOK.** Kuyruktaki örnek kayıtta
      `mbid` anahtarı dict'te bulunmuyor. Yani üç ayrı durum var: `x["mbid"]` → `KeyError`,
      `x.get("mbid")` → `None`, `x.get("mbid","")` → `""`. İlk sayfayla test eden kod
      kuyrukta patlar.

      **`image` dolu görünen boş alan.** 20 parça × 4 boyut = 80 URL beklenirken
      **4 benzersiz URL** çıktı — hepsi Last.fm'in "resim yok" varsayılanı
      (`2a96cbd8b46e442fc41c2b86b821562f.png`). Null kontrolünden geçer, içeriği çöp.
      `isna()` tipi kontroller bunu **yakalamaz**.

      **`duration == 0` belirsiz.** Parça 0 saniye mi, süre bilinmiyor mu? API ayırt
      etmiyor. Ortalama süre hesabında 0'lar sonucu bozar. `0 → null` çevrilmeli mi,
      5.4'ün kararı.

      **`@attr` sayfalama bilgisi:** `page, perPage, totalPages, total` — hepsi string.
      `total: 10000` ve `totalPages: 500` tam çarpım (500×20) veriyor, yani gerçek sayım
      değil **tavan** olma ihtimali yüksek. Son sayfanın 19 kayıt döndürmesi `total`'ın
      zaten tutarsız olduğunu gösteriyor.

      **İkinci fixture eklendi:** `chart_gettoptracks_edge_cases.json` (page=500).
      Gerekçe: mevcut fixture'da hiç edge case yoktu, 7.4'ün testleri onunla yazılamazdı.
      Dosya adı `page500` değil `edge_cases` — ad, verinin **nereden geldiğini** değil
      **ne işe yaradığını** söylemeli.

- [x] **1.6** Grain karara bağlandı. ADR-0005 yazıldı, not 14 eklendi.

      > **Bir satır = bir UTC gününde, Last.fm global top-tracks chart'ında görünen bir
      > parçanın o çekim anındaki durumu.**

      Birincil anahtar: **`(snapshot_date, artist_name, track_name)`**
      Kimball terimiyle: **periodic snapshot fact table**.

      **Ölçüm — iki anahtar adayı da tam benzersiz çıktı:**

      | Dosya | rows | `name+artist` | `url` | tekil `artist` |
      |---|---|---|---|---|
      | `..._success.json` (page=1) | 20 | 20 | 20 | **6** |
      | `..._edge_cases.json` (page=500) | 19 | 19 | 19 | 19 |

      `url` fazladan ayrım yapmıyor — aynı iki alanın URL-encode edilmiş hali.
      Seçim `(artist_name, track_name)`; `url` normal kolon olarak saklanıyor.
      Gerekçe: URL bir **kimlik değil adres**tir — anahtar yapmak veri modelini Last.fm'in
      site yapısına bağlar ve her filtreyi encode'lu string karşılaştırmasına çevirir.
      Kabul edilen bedel: isim değişirse geçmiş satırlar eski adı taşır (snapshot
      semantiğinin doğal sonucu, bug değil — veri kaybolmuyor, isim üzerinden uzun aralıklı
      join garanti edilemiyor).

      **`mbid` anahtara girmedi.** Öznitelik olarak kalıyor. Üç gerekçe: (1) kuyrukta
      4/19 kayıtta anahtar **yok**, NULL bileşenli `UNIQUE` SQL'de zorlanamaz
      (`NULL != NULL`); (2) MusicBrainz'in kimliği, Last.fm'in değil — yabancı sistemin
      anahtarı; (3) dün boş bugün dolu olabilir, anahtar değişirse aynı parça yeni kayıt
      gibi görünür. **Genel kural:** anahtara alan eklemek onu güçlendirmez, grain'i
      **inceltir** ve çiftlenme riskini artırır.

      **PROGRESS düzeltmesi — 1.5'teki ifade yanlıştı.** 1.5'te `mbid` için "%21 **boş**"
      yazılmıştı; ölçüm bunu çürüttü: `anahtar yok 4, boş string 0, dolu 15`. Yani boş
      değil, **eksik**. Kod farkı: `x.get("mbid")` → `None` riski var, `""` riski **yok**.
      5.4'te `if mbid == "":` dalı yazılmayacak. (Uyarı: `artist.mbid` ayrı ölçülmedi,
      1.5 orada "boş" demişti — 1.7'de kontrol edilecek.)

      **En kritik düzeltme — "üzerine yaz, son playcount kalsın" reddedildi.**
      İlk cevabım tek satır tutup güncellemekti. Bu SCD Type 1'dir ve burada bilgi
      imhasıdır: `playcount` **kümülatif sayaç**, günlük artış ancak iki snapshot farkından
      türetilir (`playcount(t) - playcount(t-1)`). Üzerine yazınca fark sonsuza kadar
      kaybolur. Ve `chart.getTopTracks` tarih parametresi almıyor — çekilmeyen gün
      **kalıcı boşluk**. Hata sessizdir: pipeline hiç patlamaz, aylar sonra "trend
      çıkaralım" denince verinin hiç var olmadığı anlaşılır.
      OLTP (bugünkü durumun aynası) ≠ OLAP (kaynağı zaman içinde gözlemlemek).

      **`snapshot_date` ≠ `ingested_at` — iki ayrı kolon kalıyor.** Normal koşuda
      çakışıyorlar; backfill'de ayrışıyorlar (`ingested_at` bugün, `snapshot_date` geçmiş).
      Tek kolon biri hakkında yalan söylemek zorunda kalır.

      **Gün UTC.** Tercih değil zorunluluk: ev (TRT) + iş + 9.7'de Lambda (UTC).
      `date.today()` local döner, aynı chart iki farklı `snapshot_date` alır ve anahtar
      ortamdan ortama değişir. `datetime.utcnow()` de yanlış — tz bilgisi taşımıyor.
      Doğrusu `datetime.now(timezone.utc)`.

      **Bedava gelen sonuç:** anahtara tarih girdiği için aynı günün tekrar koşusu aynı
      anahtarı üretir → `snapshot_date` partition overwrite ile satır sayısı artmaz.
      4.5, 5.7 ve 6.8 grain'den türedi, sonradan eklenmedi.

      **Artist boyut tablosu açılmadı.** Page 1'de 6 sanatçı 20 parçayı paylaşıyor, yani
      dimension savunulabilir — ama ROADMAP'te sanatçı özniteliği isteyen sorgu yok, ikinci
      tablo yazma yolunu ve idempotency yüzeyini ikiye katlar. Denormalize kalıyor.

- [x] **1.7** Hedef şema karara bağlandı. Not 15 yazıldı. 1.6'nın iki borcu kapandı.

      **Tablo:** `lastfm_chart_top_tracks_daily`
      **Grain:** bir satır = bir UTC gününde chart'ta görünen bir parçanın o andaki durumu
      **PK:** `(snapshot_date, artist_name, track_name)` — **Partition:** `snapshot_date`

      | # | kolon | kaynak yol | tip | null? | gerekçe |
      |---|---|---|---|---|---|
      | 1 | `snapshot_date` | *türetilmiş* `datetime.now(timezone.utc).date()` | `date` | hayır | Anahtar bileşeni + partition. ADR-0005. |
      | 2 | `rank` | *türetilmiş* `(page-1)*perPage + i + 1` | `int32` | hayır | Sıra hiçbir kolondan geri hesaplanamaz — ölçüldü. |
      | 3 | `artist_name` | `track.artist.name` | `string` | hayır | Anahtar bileşeni. |
      | 4 | `track_name` | `track.name` | `string` | hayır | Anahtar bileşeni. |
      | 5 | `playcount` | `track.playcount` (str→int) | `int64` | hayır | Kümülatif sayaç. Günlük artış = iki snapshot farkı. |
      | 6 | `listeners` | `track.listeners` (str→int) | `int64` | hayır | Kümülatif. `playcount >= listeners` 39/39 doğrulandı. |
      | 7 | `duration_seconds` | `track.duration` (str→int), **`0 → NULL`** | `int32` | evet | 0 = "bilinmiyor". 1.5'in açık sorusu kapandı. |
      | 8 | `track_mbid` | `track.mbid` — anahtar yoksa `None` | `string` | evet | 4/19 kayıtta anahtar **yok**. `.get()` şart. |
      | 9 | `artist_mbid` | `track.artist.mbid` — anahtar yoksa `None` | `string` | evet | Yeniden adlandırma tespitinin tek yolu. |
      | 10 | `track_url` | `track.url` | `string` | hayır | %100 türetilemiyor (35/39). Doğrulama linki. |
      | 11 | `ingested_at` | *türetilmiş* `datetime.now(timezone.utc)` | `timestamp[us, UTC]` | hayır | `snapshot_date`'ten ayrı. ADR-0005. |

      **Reddedilenler — dördü de gerekçeli:**

      | Alan | Sınav | Ölçüm |
      |---|---|---|
      | `streamable.#text`, `streamable.fulltrack` | Varyans | 39/39 kayıtta `{"#text":"0","fulltrack":"0"}`. Sıfır entropi. |
      | `image[]` (4 boyut) | Varyans | **156 URL → 4 tekil**, hepsi Last.fm placeholder'ı (`2a96cbd8...`). Non-null, dolu, tamamen boş. |
      | `artist.url` | Fonksiyonel bağımlılık | `artist_name`'den 39/39 üretilebildi. |
      | `@attr.page/perPage/totalPages/total` | Taşıma mekaniği | `rank`'in **girdisi**, sonucu değil. Raw'da kalır. |

      **1.6'nın birinci borcu kapandı — `rank` nasıl türetilecek.**
      Sıralama payload'da **hiçbir alanda yok** ve hiçbir alandan türetilemiyor. Ölçüm:

      | | idx 0 | idx 1 | idx 4 |
      |---|---|---|---|
      | page=1 `playcount` | 1.114.096 | 13.320.589 | 15.482.186 |
      | page=500 `playcount` | — | 3.531.260 | 7.681.594 |

      `playcount` da `listeners` da azalan sıralı **değil** — üstelik 500. sayfadaki bir
      parçanın `playcount`'u 1. sayfadakinden 7 kat büyük olabiliyor. Yani chart'ın
      sıralama ölçütü response'ta yok. **Bunun sonucu:** `ROW_NUMBER() OVER (ORDER BY
      playcount DESC)` ile sorgu anında türetme alternatifi **ölçümle elendi**; `rank`
      materyalize edilmek zorunda.

      Formül: `rank = (int(attr["page"]) - 1) * int(attr["perPage"]) + index + 1`

      **Global `enumerate` yanlış.** Son sayfa 20 değil **19** kayıt döndü (ölçüldü);
      sayfaları birleştirip baştan numaralandıran kod, eksik dönen her sayfadan sonra tüm
      sıraları bir kaydırır. Her sayfa kendi `@attr.page`'i ile hesaplanmalı.

      **Adım 4'e yazılan borç:** `rank` transform'da hesaplanabilir **ama yalnızca** raw
      katman (1) her sayfayı kendi kaydı olarak, birleştirmeden ve (2) `@attr`'ı atmadan
      saklarsa. Raw bunlardan birini yaparsa `rank` kalıcı olarak kurtarılamaz.
      4.x'te "@attr metadata, veri değil" deyip atmak çok doğal görünecek — görünmesin.

      **1.6'nın ikinci borcu kapandı — `artist.mbid` ölçüldü.**

      | | page=1 | page=500 |
      |---|---|---|
      | `artist.mbid` dolu | 20/20 | 18/19 (1 kayıtta anahtar yok) |
      | `track.mbid` dolu | 20/20 | **15/19** |

      Yani `artist_mbid`, anahtar olarak seçilen `track_mbid`'den **daha eksiksiz**.
      Barış önce "bunu saklamak bir şey kazandırmaz" dedi; ölçüm bunu çürüttü.
      Saklanma gerekçesi: ADR-0005'te **bilerek kabul edilen** tek zayıflık — sanatçı adı
      değişirse geçmiş satırların eski adı taşıması — yalnızca bu alanla fark edilebilir.
      Onsuz "Kanye West" ve "Ye" sonsuza kadar iki ayrı sanatçıdır ve bu geriye dönük
      olarak tespit **bile edilemez**. **Kalıyor.**

      **`track_url` — burada ben (Claude) yanıldım, ölçüm düzeltti.**
      "url zaten `artist_name` + `track_name`'den türetilebilir, atılmalı" dedim. Test:

      ```
      quote_plus ile yeniden üretilebilen: 35 / 39
      ```

      Tutmayan 4 kayıt: Last.fm `(` `)` `$` `,` karakterlerini kaçırmıyor, `quote_plus`
      kaçırıyor. Yani url **Last.fm'in kendi encode kurallarını** taşıyor, RFC'nin değil.
      Türetseydik kayıtların ~%10'unda **sessizce** kırık link üretirdik. **Saklanıyor** —
      ADR-0005'in "url normal kolon olarak kalır" kararıyla da tutarlı.

      **`duration_seconds` için `0 → NULL` kabul edildi.** Gerekçe: belirsizliği veri
      katmanında bir kere çözmek. 0'ı olduğu gibi saklarsan o kolona dokunan *her* sorgu
      `WHERE duration > 0` filtresini hatırlamak zorunda kalır ve biri unutur.

      **Tip kararlarının gerekçeleri** (detay → not 15 §3): `playcount`/`listeners` →
      `int64` çünkü kaynağın kümülatif sayacı, tavanını biz belirlemiyoruz ve Parquet
      encoding sonrası dar tip yer kazandırmıyor, sadece sessiz taşma riski veriyor.
      `duration_seconds` → `int32`, burada dar tip **kasıtlı bir üst sınır ifadesi**.
      `snapshot_date` → `date`, `timestamp` değil: **tip, grain'i ifade eden bir
      sözleşmedir**. Hiçbir kolonda `category` yok — `artist_name` kardinalitesi page=1'de
      6/20, page=500'de 19/19; tek örnekten kategori tipi seçmek klasik hata.

      **`NOT NULL` bir alarm olarak konuldu**, tahmin olarak değil: anahtar bileşenleri ve
      ölçüler boş gelirse **yazma patlamalı**. Bozuk veri erken ve gürültülü patlamalı,
      geç ve sessiz değil.

- [ ] **1.8** Rate limit — **devam ediyor.** Aktif sondaj iptal, kapsam kararı alındı
      (ADR-0006). İki küçük ölçüm kaldı, aşağıda.

      **Header ölçümü — boş sonuç, ama kayda değer bir bulgu.**
      `curl -sS -D - -o /dev/null ... | grep -i -E 'ratelimit|retry-after|x-rate'` →
      **hiçbir şey**. Ne `Retry-After`, ne `RateLimit-*`, ne `X-RateLimit-*`.
      Sonucu: 3.4'teki backoff süresi **istemci tarafında hesaplanacak**, sunucudan
      okunamayacak. Bedava gelen bilgi yoktu, kendimiz üreteceğiz.

      **Belgelenen limit (ikinci el kaynak — birincil ToS sayfası doğrulanmadı):**
      *"saniyede 5 istek, originating IP başına, 5 dakikalık ortalama üzerinden"*,
      artı ayrı bir **frequency cap** maddesi: sürekli saniyede birkaç istek veya ani
      sıçrama, API hesabının askıya alınma sebebi. İki cümle gerilimde — 5/s serbest
      ama "sürekli birkaç/sn" cezalı. Okunuşu: **5/s bir tavandır, hedef değildir.**

      **Kapsam belirsizliği çözüldü: limit IP başına.** 9.7'yi etkiliyor — Lambda'nın
      dönen IP'leri ayrı kova demek, ama ev + iş aynı IP'den giderse aynı kova.
      (Öncesinde iki çelişkili ifade vardı: unofficial docs "your IP", gerçek hata
      metni "this application".)

      **Aktif sondaj yapılmadı — bilinçli.** İki katmanlı gerekçe: (1) doküman sayıyı
      ve kapsamı veriyor, (2) ADR-0006'dan sonra günlük istek ~5, yani limit bağlayıcı
      bir kısıt değil. Sondajın bedeli sıfır değil: aşırı kullanım cezası hata kodu
      **26 — "your API key has been banned"**. Riski olmayan aşamalar cevabı verdiği
      için riskli aşamaya geçilmedi. Protokol → not 17 §2.

      **`limit` parametresi ölçüldü — sayfalama semantiğini değiştiriyor.**

      | İstek | `perPage` | `totalPages` | `total` | kayıt |
      |---|---|---|---|---|
      | `limit=20` | `20` | `500` | `10000` | 20 |
      | `limit=100` | `100` | `100` | `10000` | 100 |

      **1.5'in şüphesi doğrulandı:** `total: 10000` gerçek bir sayım değil, sabit bir
      **tavan**. `totalPages = total / perPage`. İki farklı `limit` ile `total`
      değişmiyor, `totalPages` değişiyor.

      **`rank` üzerindeki sonucu kritik:** `perPage` artık sunucunun sabit bir özelliği
      değil, **bizim gönderdiğimiz bir parametre**. 1.7'de "junior tuzağı" diye yazılan
      *"`perPage`'i 20 diye sabit yazmak"* artık varsayımsal değil — sayfa boyutunu
      değiştiren taraf biziz. Formül `@attr`'dan okunduğu sürece doğru kalır; sabit
      yazılırsa config değiştiği gün **sessizce** bozulur.

      **Kapsam kararı: top 100 → ADR-0006.** Günlük ~500 istek yerine ~5.
      Seçilen yol tek istekle `limit=100` **değil**, hedef sayıya kadar sayfalama.
      Gerekçe: `limit=100` ölçüldü ve bugün çalışıyor, ama doğruluğu kontrol
      etmediğimiz bir sunucu parametresine bağlıyor — Last.fm `limit`'i kırparsa cevap
      **sessizce kısa** gelir, hata fırlamaz. Hedef sayıya kadar döngü, sunucu
      `perPage`'i ne yaparsa yapsın doğru çalışır. Ayrıca sayfalama kodu her koşuda
      birkaç kez çalışır, yani ölü kod olmaz.

      **ROADMAP revize edildi:** 3. adımda sayfalama alt adımı **hiç yoktu** — 3.9
      olarak eklendi. Araya sokulmadı, sona eklendi: `3.7` başka dosyalardan referanslı
      (not 11, PROGRESS 1.2), yeniden numaralamak o bağlantıları sessizce kırar.
      **Numara bir kimliktir, sıra değildir** — ADR'lerin asla yeniden numaralanmama
      gerekçesiyle aynı.

      **Kalan iki ölçüm:**

      1. **Pasif gecikme ölçümü** — 20 ardışık istek (not 17 §2, aşama 3 script'i).
         Amacı limit bulmak değil: 3.2'deki `timeout` değerinin gerçek verisi.
         Timeout'u tahminle koymak yaygın ve yanlış.
      2. **Tarih parametresi testi** — ADR-0005 ve ADR-0006 *"`chart.getTopTracks`
         tarih parametresi almıyor"* varsayımına dayanıyor ve bu **hâlâ ölçülmedi**;
         iddia API dokümanına dayanıyor. Doğruysa backfill yalnızca raw katmandan
         yapılabilir — yani ADR-0006'nın "kaçırılan gün kalıcı kayıptır" maddesi buna
         bağlı. Test: bir tarih parametresi ekleyip cevabın değişip değişmediğine bakmak.

## Açık sorular

- Build backend `setuptools` seçildi; `uv` bir build backend değil (resolver + paket
  yöneticisi), dolayısıyla ADR-0003 bu kararı değiştirmiyor. `hatchling` alternatifi
  açık kalmaya devam ediyor; değişirse ADR yazılır.
- `.python-version` yok. `requires-python = ">=3.11"` bir aralık — iki makinede farklı
  yorumlayıcı seçilebilir (ev: 3.14.5). Sapma görülürse `uv python install` +
  `.python-version` ile sabitlenecek. Şimdilik bilinçli olarak eklenmedi.
- CI **bu turun kapsamında değil** (`ROADMAP.md` → Sonraki tur). Kurulduğunda `uv`'nin
  **kendi sürümü** de sabitlenmeli. Bağımlılıkları kilitleyip
  aracı kilitlememek, "kendiliğinden bozulan build" riskini açık bırakır.
- **Chart'ın sıralama ölçütü bilinmiyor.** 1.7'de ölçüldü: sıra ne `playcount` ne
  `listeners` ile uyumlu, 500. sayfada 1. sayfadan büyük `playcount`'lar var. Yani chart
  muhtemelen **son dönem** aktivitesine göre sıralı, `playcount` ise **tüm zamanlar**
  kümülatif. Aynı satırda iki farklı zaman semantiği taşınıyor. Bu bir hata değil ama
  analiz yapılırken (`rank` ile `playcount` birlikte yorumlanırken) bilinmesi gerek.
  Doğrulanamaz — Last.fm ölçütü belgelemiyor. Şema notu olarak kalsın.
- **`rank` bazı SQL lehçelerinde ayrılmış kelime.** Athena/Presto'da `RANK()` bir pencere
  fonksiyonu. Kolon adı olarak sorun çıkarırsa `chart_rank`'e dönülecek. → **P4.2**'de test (Athena).
- **P2.2'ye devredilen borç:** raw katman her sayfayı **ayrı** ve `@attr` ile birlikte
  saklamak zorunda; aksi halde `rank` kalıcı olarak kurtarılamaz hale gelir. Bu bir
  "açık soru" değil, unutulması muhtemel bir **kısıt**. → **P2.2**.
- **Aynı gün içinde sayfa kayması.** Chart sayfalar çekilirken yeniden sıralanırsa aynı
  parça iki sayfada görünebilir ve anahtar tek `snapshot_date` içinde çakışır. Gözlenmedi
  (iki fixture farklı sayfalar, kesişim yok) ama çürütülmedi de. → **P2.3 / P2.4**.
- **`chart.getTopTracks` tarih parametresi almıyor** iddiası API dokümanına dayanıyor,
  ölçülmedi. **Bu soru artık kararı değiştirmiyor** — backfill ve CLI zaten iptal
  (`ROADMAP.md` → Sonraki tur). P2.1'de client yazılırken 2 dakikada teyit edilebilir; edilmezse de
  plan aynı kalır. Kapatıldı.

## Git geçmişinde görünmeyen kararlar

- Veri gölü `/data/` altında yaşar ve gitignore'ludur. Klasör yapısı ileride kurulacak
  S3 yapısını (`raw/`, `curated/`) birebir taklit eder — böylece AWS'ye taşırken yol
  mantığı değişmez.
- `docs/notes/` Türkçe (öğrenme defteri), `docs/adr/` İngilizce (portfolyo çıktısı).
- `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı. Tek kaynak burasıdır.

## Sonraki oturum için hatırlatma

- Oturuma `git pull` ile başla, `git push` ile bitir. İki makinede çalışılıyor.
- `git pull` sonrası `git status` **temiz** olmalı. Kirliyse `.gitattributes` o makinede
  uygulanmamış demektir — `git ls-files --eol` ile bak.
- **`uv` her iki makinede de kurulu** (ev + iş). Yeni bir makinede `uv sync` şart.
- **`.env` git'e girmez** — her makinede elle oluşturulur. Yeni makinede ilk iş:
  `.env.example`'ı kopyalayıp gerçek key'i yazmak.
- `curl` çağrılarından önce `.env`'i oturuma yükle (`docs/notes/11` §3). Sır komut
  satırına elle yazılmaz.
- **Adım 1 bitti.** P1 hesap/sır kurulumu; **P2'den itibaren** bir oturumun çıktısı
  `src/` altında çalışan koddur. Oturum sonunda `src/` boşsa o oturum kapsam
  tartışmasına gitmiştir; `PROJECT_CONTEXT.md` §1b'yi aç.
- **Not koddan sonra yazılır.** Bir alt adıma not yazarak başlanıyorsa sıra ters.

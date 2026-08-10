# 09 — `uv` iş akışları ve klasik karşılıkları

> Adım 0.4 · 2026-08-10

Not 08 **kavramları** anlatıyor: sanal ortam neyi çözüyor, editable install nedir, lock
dosyası niye var. Bu not onun üstüne **pratiği** koyuyor: hangi komut, hangi sırayla,
neden o sırayla — ve `uv` olmayan bir makinede aynı işin nasıl yapıldığı.

İkisini birlikte oku. 08 "neden", 09 "nasıl".

---

## 1. Zihinsel model: emir kipi vs bildirim kipi

`uv`'nin komutlarını ezberlemeden önce şu ayrımı oturt. Her paket yöneticisi bu ikisinden
birine düşer:

| | **Emir kipi** (imperative) | **Bildirim kipi** (declarative) |
|---|---|---|
| Ne söylersin | "Şunu kur" | "Ortam şu olsun" |
| Örnek | `pip install requests` | `uv sync` |
| Doğruluk kaynağı | Terminalde yazdığın komut | `uv.lock` dosyası |
| Fazlalık paket | **Kalır** | **Silinir** |
| Ortamın durumu | Komut geçmişinin toplamı | Tek dosyadan okunabilir |

Fark neden önemli: emir kipinde ortamın hâli, aylar boyunca yazdığın komutların
**birikmiş sonucudur**. Kimse o geçmişi hatırlamaz. `pip install -r requirements.txt`
hiçbir zaman bir şey **silmez** — bir bağımlılığı listeden çıkarsan bile ortamında
durmaya devam eder.

Somut senaryo:

| An | Senin makinen | Temiz kurulum (CI, yeni arkadaş) |
|---|---|---|
| `pip install pandas` | pandas var | — |
| Koddan pandas'ı çıkardım, `requirements.txt`'ten sildim | **pandas hâlâ ortamda** | pandas yok |
| Ama bir dosyada `import pandas` unutulmuş | Çalışır | `ModuleNotFoundError` |

"Bende çalışıyordu"nun kaynağı budur. `uv sync` ortamı lock dosyasının **aynası** yapar;
lock'ta olmayan paket ortamda **kalamaz**. Bu yüzden problem yapısal olarak imkânsızlaşır.

### Bunun sonucu: bir komut kuralı

> Ortamı değiştiren her şey `pyproject.toml` + `uv.lock` üzerinden geçmeli.
> Ortama **doğrudan** kurulum yapan komut kullanılmaz.

Pratikte: `uv add` kullan, `uv pip install` kullanma. Sebebi §9'da.

---

## 2. Önce `uv`'nin kendisi: bootstrap problemi

`uv`, sanal ortamı **oluşturan** araç. Dolayısıyla sanal ortamın içine kurulamaz —
tavuk-yumurta. **Sisteme kurulur.**

Daha güçlü ikinci sebep: `uv` bir Python paketi **değil**. Rust ile yazılmış tek bir
binary. Çalışmak için Python'a ihtiyacı yok; hatta Python'un kendisini indirebiliyor.

### Barış önce şöyle sandı

*"Python aracıysa `pip install uv` ile kurulur."*

**Teknik olarak çalışır ama yanlış.** Aracı, yönetmesi gereken şeye bağımlı hâle
getirirsin. O Python kurulumunu silersen `uv` de gider. Ayrıca hangi Python'un
`site-packages`'ında durduğu belirsizleşir.

### Doğru kurulum yolları

| Platform | Yöntem | Komut | Güncelleme |
|---|---|---|---|
| Windows | winget | `winget install --id=astral-sh.uv -e` | `winget upgrade` |
| Windows | Standalone installer | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` | `uv self update` |
| macOS / Linux | Standalone installer | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv self update` |
| macOS | Homebrew | `brew install uv` | `brew upgrade` |

Trade-off: standalone installer `uv self update`'i açar. Sistem paket yöneticisiyle
(winget, brew) kurarsan `uv self update` **çalışmaz** — `uv` bunu algılayıp seni paket
yöneticisine yönlendirir. Bu kasıtlı bir tasarım: iki güncelleme mekanizmasının aynı
binary üzerinde çakışmasını engelliyor.

Bu projede winget seçildi. Sebep: sistem araçları tek yerden yönetilsin. Bu bir tercih,
sektör standardı değil.

### Kurulumdan sonra: terminali kapat aç

`PATH` bir ortam değişkeni ve **süreç başlarken kopyalanır**. Açık terminalin,
kurulumdan *önceki* `PATH`'in fotoğrafını taşır. Yeni kurulan binary orada görünmez.

Bu, `activate`'in yaptığı işin (bkz. not 08 §2) aynısının tersten görünüşü: her ikisi de
`PATH`'in süreç başında dondurulmasıyla ilgili.

---

## 3. Senaryo bazlı akışlar

Asıl bölüm burası. Sol sütun `uv`, sağ sütun `uv` olmayan bir makinede aynı iş.

### A. Sıfırdan yeni proje

| Adım | `uv` | Klasik (`venv` + `pip` + `pip-tools`) |
|---|---|---|
| 1. İskelet | `uv init --package myproj` | Klasörleri elle aç, `pyproject.toml`'u elle yaz |
| 2. Ortam | `uv venv` (ya da doğrudan `uv sync`) | `python -m venv .venv` |
| 3. Aktivasyon | **Gerekmez** — `uv run` halleder | `source .venv/bin/activate` |
| 4. Projeyi kur | `uv sync` (editable kurulum dahil) | `pip install -e .` |
| 5. Bağımlılık ekle | `uv add requests` | `requirements.in`'e elle yaz → `pip-compile` → `pip-sync` |

`uv init` bu projede kullanılmadı — `pyproject.toml` 0.3'te elle yazıldı. Kasıtlı:
üretilen dosyayı okumakla, dosyayı yazmak farklı şeyler öğretir.

### B. Var olan repoyu klonladım (en sık senaryo)

İki makinede çalışıyorsan bu akışı her gün kullanacaksın.

```bash
git clone <url>
cd <repo>
uv sync
```

**Üç komut. Bitti.** `uv sync` şunları yapar: uygun Python'u bulur (yoksa indirir),
`.venv/` oluşturur, `uv.lock`'taki **tam** sürümleri kurar, projeyi editable bağlar.

Klasik karşılığı:

```bash
git clone <url>
cd <repo>
python -m venv .venv                    # dogru Python surumu sende var mi? Belirsiz
source .venv/bin/activate               # Windows'ta farkli komut
pip install -r requirements.txt         # transitive surumler serbest -> sapma
pip install -e .                        # ayri adim
```

Fark sadece satır sayısı değil. Klasik yolda dört ayrı yerde sessizce yanlış gidebilir:
yanlış Python sürümü, yanlış shell komutu, lock'suz kurulum, unutulan editable adım.

### C. Yeni bağımlılık ekliyorum

```bash
uv add requests
uv add "requests>=2.28,<3"    # aralik belirterek
uv add --dev pytest ruff mypy # sadece gelistirme icin
```

`uv add` **üç işi birden** yapar ve bu üçünün ayrılmaması kritik:

1. `pyproject.toml`'a yazar (abstract aralık)
2. `uv.lock`'u günceller (concrete sürümler + hash'ler)
3. Ortama kurar

Klasik yolda bu üçü ayrı adımdır ve **biri unutulur**. En sık unutulan 1. madde: paketi
`pip install` ile kurarsın, çalışır, `pyproject.toml`'a yazmayı unutursun. Senin makinende
her şey yolunda; CI'da `ModuleNotFoundError`.

| | `uv` | Klasik |
|---|---|---|
| Runtime bağımlılığı | `uv add requests` | `pyproject.toml`'u elle düzenle + `pip install -e .` |
| Dev bağımlılığı | `uv add --dev pytest` | Ayrı `requirements-dev.txt` + ayrı `pip install -r` |
| Nereye yazılır | `[project.dependencies]` / `[dependency-groups]` | Dosya sayısı projeye göre değişir, konvansiyon yok |

`--dev` ile eklenenler **PEP 735** `[dependency-groups]` bölümüne gider. Bu 2024'te kabul
edilmiş bir Python standardı — `uv`'ye özel bir icat değil. Amacı: `pytest` ve `ruff`
üretim ortamına gitmesin. Docker image'ında `uv sync --no-dev` dersin, test araçları
image'a hiç girmez.

### D. Bağımlılık kaldırıyorum

```bash
uv remove requests
```

`pyproject.toml`'dan siler, lock'u yeniden çözer, **ortamdan da kaldırır** — artık
kimsenin ihtiyaç duymadığı transitive paketlerle birlikte.

Klasik yolda `pip uninstall requests` sadece `requests`'i siler; `urllib3`, `certifi`,
`idna` ortamda **öksüz kalır**. Zamanla ortamın gerçek içeriğiyle beyanın arası açılır.

### E. Bağımlılıkları güncelliyorum

| Amaç | Komut |
|---|---|
| Her şeyi aralıklar içinde en yeniye çek | `uv lock --upgrade` |
| Tek paketi güncelle | `uv lock --upgrade-package requests` |
| Lock'u değiştirmeden ortamı eşitle | `uv sync --frozen` |

Ayrım önemli:

- **`uv lock`** → "hangi sürümler kurulmalı" sorusunu çözer, dosyaya yazar. **Ortama
  dokunmaz.**
- **`uv sync`** → lock'u okur, ortamı ona **eşitler**.

Klasik karşılığı `pip-compile --upgrade` (pip-tools) — ama pip-tools sadece bunu yapar,
ortam ve Python sürümü yönetimi ayrı araçların işi kalır.

### F. Bir komut çalıştırıyorum

```bash
uv run python script.py
uv run pytest
uv run ruff check .
```

`uv run` çalıştırmadan **önce** ortamın lock ile uyumlu olduğunu kontrol eder, gerekirse
senkronize eder, sonra komutu çalıştırır. `activate` gerekmez.

Klasik karşılığı: `source .venv/bin/activate` → komut. Ya da `.venv/bin/python script.py`.

**Ne zaman `activate` yine de mantıklı:** uzun bir çalışma oturumunda arka arkaya onlarca
komut çalıştırıyorsan, her seferinde `uv run` yazmak yorucudur. `activate` hâlâ geçerli
bir seçenek — `uv` onu yasaklamıyor, sadece zorunlu olmaktan çıkarıyor.

**Junior tuzağı:** `uv run` her şeyi hallettiği için `PATH`, `pyvenv.cfg`, `sys.prefix`
mekanizmasını hiç öğrenmeden proje geliştirmek mümkün. Sonra CI veya Docker'da bir şey
kırıldığında teşhis edilemez hâle gelir. Not 08 §2 tam bu riske karşı yazıldı.

### G. CI'da (GitHub Actions — Adım 8.5)

```yaml
- uses: astral-sh/setup-uv@vX   # action surumu 8.5'te guncel haliyle yazilacak
  with:
    version: "0.12.2"           # uv'nin kendi surumu -> SABITLE
- run: uv sync --frozen
- run: uv run pytest
```

İki kritik nokta:

**`--frozen`**: lock dosyasını **güncellemez**. `pyproject.toml` ile `uv.lock` arasında
tutarsızlık varsa hata verip durur. Bu istenen davranıştır — CI'ın işi sapmayı sessizce
tamir etmek değil, **görünür kılmaktır**. `--frozen` olmadan CI lock'u kendi günceller,
sen fark etmezsin, ve lokalinle CI farklı şeyler kurar.

**`version: "0.12.2"`**: `uv`'nin kendi sürümünü sabitle. Aksi hâlde bir gün Astral
resolver davranışını değiştirir ve sen hiçbir şeye dokunmadığın hâlde build kırılır.
ROADMAP 8.6'daki "bir gün kendiliğinden bozulan build" tam olarak budur — ve araç
zincirinin kendisi de bu riske dahildir, sadece bağımlılıklar değil.

Klasik karşılığı: `actions/setup-python` + `pip install -r requirements.txt`. Lock yok,
`--frozen` gibi bir güvenlik ağı yok.

### H. Docker'da (Adım 8.7)

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

WORKDIR /app
# Once sadece manifest'leri kopyala: kod degisince bagimlilik katmani yeniden kurulmaz
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev
```

Buradaki fikir `uv`'ye özel değil, **Docker layer cache** mantığı: en az değişen şey en
üstte olur. Kaynak kodun her commit'te değişir, bağımlılıkların ayda bir. İkisini aynı
`COPY` ile alırsan her commit'te tüm bağımlılıklar yeniden kurulur.

| Flag | Ne yapar |
|---|---|
| `--frozen` | Lock'u güncelleme, uyumsuzsa patla |
| `--no-dev` | `[dependency-groups]` içindekileri kurma — `pytest` image'a girmesin |
| `--no-install-project` | Sadece bağımlılıkları kur, projeyi kurma (cache katmanı için) |
| `UV_COMPILE_BYTECODE=1` | `.pyc` dosyalarını build'de üret → cold start hızlanır (Adım 9.5, Lambda) |
| `UV_LINK_MODE=copy` | Hardlink yerine kopyala — Docker'da farklı mount'lar arası hardlink kurulamaz |

Prod'da `-e` (editable) **kullanılmaz** (not 08 §3). `uv sync` prod modunda projeyi
normal kurar.

### I. Python sürümünün kendisi

İki makine kullanıyorsan gerçek bir problem: evde 3.14, işte 3.11 olabilir.

```bash
uv python list           # sistemde ne var, uv ne indirebilir
uv python install 3.12   # yorumlayicinin kendisini indirir
uv venv --python 3.12    # o surumle ortam kur
```

`.python-version` dosyası projeye sürüm sabitler; `uv` bu dosyayı görürse o sürümü
kullanır, yoksa indirir. Klasik karşılığı `pyenv` — ayrı bir araç, Windows'ta
sancılıdır (`pyenv-win` ayrı bir proje).

Bu projede henüz `.python-version` yok. `requires-python = ">=3.11"` bir **aralık**;
iki makinede farklı sürüm seçilmesine izin verir. Sapma görülürse eklenecek.

---

## 4. `uv sync` tam olarak ne yapıyor

Tek komut ama altında altı adım var. Bir şey ters gittiğinde hangi adımda olduğunu
bilmek gerekir:

1. `pyproject.toml`'u okur, `requires-python`'a uyan bir yorumlayıcı arar
   (`.python-version` varsa onu kullanır, yoksa sistemde arar, bulamazsa indirir)
2. `.venv/` yoksa oluşturur, `pyvenv.cfg` yazar
3. `uv.lock` yoksa veya `pyproject.toml` ile tutarsızsa **yeniden çözer ve yazar**
   (`--frozen` verilmişse bunun yerine hata verir)
4. Lock'taki paketleri kurar
5. Lock'ta **olmayan** paketleri ortamdan **siler**
6. Projenin kendisini editable kurar (`[build-system]` varsa)

Klasik yolda bu altı adım sırasıyla: `pyenv` + `python -m venv` + `pip-compile` +
`pip-sync` + `pip install -e .` — dört ayrı araç.

---

## 5. `uv.lock` anatomisi

Bu projenin `dependencies = []` iken üretilen ilk lock dosyası:

```toml
version = 1
revision = 3
requires-python = ">=3.11"

[[package]]
name = "lastfm-etl"
version = "0.1.0"
source = { editable = "." }
```

Boş değil — ve bu şaşırtıcı gelebilir. Satır satır:

| Alan | Anlamı |
|---|---|
| `version = 1` | Lock **formatının** sürümü. `uv` güncellendiğinde format değişirse buradan anlaşılır |
| `revision = 3` | Aynı format içindeki küçük revizyon |
| `requires-python` | `pyproject.toml`'dan kopyalandı. Lock'un hangi Python aralığı için çözüldüğü |
| `[[package]]` | Her paket için bir blok. Şu an tek paket var: **projenin kendisi** |
| `source = { editable = "." }` | Bu paket bir yerden indirilmedi; bulunduğun klasörden editable kuruldu |

Öğrenilecek şey: **proje kendi lock dosyasında bir paket olarak görünür.** `uv` projeyi
"özel bir şey" olarak değil, bağımlılık grafiğinin bir düğümü olarak modelliyor. Bu,
ileride monorepo / workspace yapısına geçilirse (birden çok paket, ortak lock) aynı
modelin ölçeklenmesini sağlıyor.

`uv add requests` dedikten sonra bu dosya `requests`, `urllib3`, `certifi`,
`charset-normalizer`, `idna` bloklarıyla ve her biri için `wheels = [{ url = ..., hash =
"sha256:..." }]` satırlarıyla dolacak. **Hash'ler** supply-chain saldırısına karşı
savunmadır: indirilen dosyanın beklenen dosya olduğunu kanıtlar.

`uv.lock` **commit edilir.** Türev bir dosya olduğu hâlde — çünkü onun görevi zaten
"türetmeyi tekrarlanabilir kılmak". Not 01'deki "türetilebilen hiçbir şey git'e girmez"
kuralının bilinçli istisnası: lock dosyası türevin **kendisi** değil, türevin **tarifi**.

---

## 6. `uv`'nin ürettiği `pyvenv.cfg` ile `venv`'inki

Aynı makinede, aynı Python ile üretilen iki dosya:

**`python -m venv .venv-test`:**
```ini
home = C:\Python314
include-system-site-packages = false
version = 3.14.5
executable = C:\Python314\python.exe
command = C:\Python314\python.exe -m venv C:\...\.venv-test
```

**`uv sync`:**
```ini
home = C:\Python314
implementation = CPython
uv = 0.12.2
version_info = 3.14.5
include-system-site-packages = false
prompt = lastfm-etl
```

| Alan | `venv` | `uv` | Not |
|---|---|---|---|
| `home` | var | var | **İkisinde de aynı.** İzolasyonun temeli değişmiyor |
| `include-system-site-packages` | var | var | Aynı |
| Sürüm | `version` | `version_info` | Aynı bilgi, farklı anahtar |
| `executable`, `command` | var | yok | PEP 405'te opsiyonel |
| `implementation` | yok | var | CPython / PyPy ayrımı |
| `uv` | yok | var | Ortamı hangi araç üretti |
| `prompt` | yok | var | `activate`'te görünecek isim — `pyproject.toml`'daki proje adından |

**Çıkarılacak sonuç:** `uv` yeni bir ortam formatı icat etmiyor. Aynı PEP 405 dosyasını,
birkaç ek alanla yazıyor. Bu, ADR-0003'teki "bırakma maliyeti düşük" iddiasının somut
kanıtı — `uv`'yi silsen `.venv/` klasörü standart bir venv olarak çalışmaya devam eder.

Bir de pratik sonuç: `uv` alanı sayesinde bir ortamın hangi `uv` sürümüyle üretildiği
dosyanın içinde yazıyor. Altı ay sonra "bu ortam nereden geldi" sorusunun cevabı burada.

---

## 7. Teşhis: `command not found`

`uv --version` → `bash: uv: command not found`. Bu mesaj **iki farklı** şey demek olabilir
ve ayırt etmeden düzeltmeye kalkmak zaman kaybıdır:

| Olasılık | Nasıl anlaşılır |
|---|---|
| Binary hiç kurulmadı | Kurulum çıktısında hata vardı; dosya diskte yok |
| Kuruldu ama `PATH`'te görünmüyor | Dosya diskte var; `PATH` eski |

Teşhis komutları:

```bash
which uv                              # hangi dosya calisiyor (Unix/Git Bash)
where uv                              # ayni is (Windows cmd/PowerShell)
echo $PATH | tr ':' '\n'              # PATH'i satir satir dok (Git Bash)
$env:PATH -split ';'                  # ayni is (PowerShell)
```

`which` alışkanlığını şimdi edin. İleride şu senaryoyla karşılaşacaksın: venv aktifken
`python` yazıyorsun ama sistem Python'u çalışıyor. Teşhis komutu aynı: `which python`.

> `PATH` bir listedir ve **ilk eşleşen kazanır**. İki `python.exe` varsa hangisinin
> çalıştığı tamamen sıralamaya bağlıdır.

Bu projede yaşanan somut vaka: winget `uv`'yi `Links/` klasörüne shim koymadı, kendi
`Packages/astral-sh.uv_.../` klasörünü doğrudan `PATH`'e ekledi. `Links/`'e bakan tahmin
yanlış çıktı; `which uv` gerçeği söyledi. **Ders: tahmin etme, ölç.**

---

## 8. Windows'ta shell farkı

Aynı makinede üç shell var ve komut sözlükleri farklı:

| İş | CMD | PowerShell | Git Bash |
|---|---|---|---|
| Klasör listele | `dir` | `dir` / `Get-ChildItem` | `ls` |
| Klasör sil (recursive) | `rmdir /s /q x` | `Remove-Item -Recurse -Force x` | `rm -rf x` |
| Ortam değişkeni | `%PATH%` | `$env:PATH` | `$PATH` |
| Venv aktive et | `.venv\Scripts\activate.bat` | `.venv\Scripts\Activate.ps1` | `source .venv/Scripts/activate` |

`python -m venv` üçünde de aynı çalışır — çünkü o Python'un işi, shell'in değil. Ama
`rm` / `Remove-Item` shell'e aittir.

**Prod'da ne kırılır:** README'ye "şu komutu çalıştır" yazarken hangi shell'i
varsaydığını belirtmezsen, projeni klonlayan kişi ilk adımda takılır. Profesyonel repolar
bunu iki yoldan çözer: ya tek shell varsayıp açıkça yazar, ya da `make` gibi bir katmanla
shell farkını gizler. Bu projede Adım 8.3'te `Makefile` gelecek — asıl sebebi bu.

`uv run` bu problemi kısmen çözüyor: `uv run pytest` üç shell'de de aynı, çünkü
`activate` gerekmiyor.

---

## 9. Kaçınılacaklar

| Yapma | Neden | Onun yerine |
|---|---|---|
| `pip install uv` | Aracı, yönetmesi gereken şeye bağlar | winget / brew / standalone installer |
| `uv pip install X` (project mode'da) | pip uyumluluk katmanı; **`uv.lock`'a hiç bakmaz**. Kurduğun sürümle lock'takinin aynı olduğunu hiçbir şey garanti etmez | `uv add X` |
| `.venv/` içindeki `pip`'i doğrudan çağırmak | Aynı sebep — lock bypass edilir | `uv add` / `uv sync` |
| `uv.lock`'u `.gitignore`'a koymak | Reproducibility'nin tamamı o dosyada | Commit et |
| `uv.lock`'u elle düzenlemek | Hash'ler ve çözüm grafiği tutarlı olmalı | `uv lock --upgrade-package X` |
| CI'da `uv sync` (`--frozen` olmadan) | Sapmayı sessizce tamir eder, sen görmezsin | `uv sync --frozen` |
| CI'da `uv` sürümünü sabitlememek | Araç güncellenince build kendiliğinden kırılabilir | `version:` alanını yaz |
| `pyproject.toml`'a `==` ile pin | Abstract/concrete karışır (not 08 §4) | Aralık yaz, pin lock'ta kalsın |

`uv pip install` neden var o zaman? Var olan pip tabanlı projelerin `uv`'ye hızlı geçişi
için. Yeni bir projede project mode kullanıyorsan, o komuta dönmek ADR-0003'te
**reddedilen** modele geri dönmektir.

---

## 10. Cheatsheet

```bash
# --- ortam ---
uv sync                      # lock'tan ortami kur/esitle (en cok kullanacagin komut)
uv sync --frozen             # lock'u guncelleme, uyumsuzsa patla (CI)
uv sync --no-dev             # dev bagimliliklarini atla (Docker/prod)
uv venv --python 3.12        # belirli surumle ortam kur

# --- bagimlilik ---
uv add requests              # ekle: pyproject + lock + kurulum
uv add --dev pytest          # dev bagimliligi (PEP 735)
uv remove requests           # kaldir: pyproject + lock + ortam
uv lock                      # sadece coz ve yaz, ortama dokunma
uv lock --upgrade            # araliklar icinde en yeniye cek
uv tree                      # bagimlilik agaci

# --- calistirma ---
uv run python script.py
uv run pytest

# --- python surumu ---
uv python list
uv python install 3.12

# --- disari aktarma ---
uv export --format requirements-txt > requirements.txt

# --- teshis ---
which uv
uv --version
cat .venv/pyvenv.cfg
```

Günlük akış, sadeleştirilmiş hâli:

```
git pull  ->  uv sync  ->  <calis>  ->  uv add X (gerekirse)  ->  git add uv.lock  ->  commit  ->  git push
```

`uv add` yaptığın her seferde **`uv.lock`'u da commit et.** İkisi ayrı commit'lere
düşerse, arada bir noktada `pyproject.toml` ile lock tutarsız kalır — ve o commit'i
checkout eden kişide `uv sync --frozen` patlar.

---

## 11. Mülakat

**"`uv sync` ile `pip install -r requirements.txt` arasındaki fark ne?"**
→ *"`uv sync` deklaratif: ortamı lock dosyasının aynası yapar, lock'ta olmayan paketi
siler. `pip install -r` emir kipi ve hiçbir zaman bir şey silmez — ortam, geçmişte
çalıştırılan komutların birikimi olur. 'Bende çalışıyor' problemi buradan doğar."*

**"CI'da neden `--frozen`?"**
→ *"Lock ile `pyproject.toml` arasındaki tutarsızlığı sessizce tamir etmek yerine hata
verdirmek için. CI'ın işi sapmayı görünür kılmak. Ayrıca aracın kendi sürümünü de
sabitleriz — resolver davranışı değişince build hiçbir değişiklik olmadan kırılabilir."*

**"Lock dosyası türev bir dosya, neden commit ediliyor?"**
→ *"Çünkü türevin kendisi değil, türetmenin tarifi. Amacı farklı makinede ve farklı
zamanda birebir aynı ortamı üretebilmek. Uygulamalarda commit edilir; kütüphanelerde
edilmez, çünkü kütüphaneyi kuran kişinin kendi çözümünü yapması gerekir."*

**"`uv`'ye bağımlı kalmaz mısın?"**
→ *"Düşük risk. Standart `pyproject.toml` okuyor ve ürettiği `.venv/` standart bir PEP 405
ortamı — `pyvenv.cfg`'de sadece birkaç ek alan var. Bırakmak `uv.lock`'u silip başka bir
resolver seçmek demek; `pyproject.toml` etkilenmez."*

---

## Sözlük eki

Not 08'in sözlüğüne ek olarak:

| Terim | Anlamı |
|---|---|
| **bootstrap problemi** | Bir aracın, kuracağı şeye kendisinin ihtiyaç duyması. `uv` venv oluşturur, o yüzden venv'in içine kurulamaz |
| **declarative / imperative** | "Sonuç şu olsun" (bildirim) vs "şu adımı yap" (emir). `uv sync` birincisi, `pip install` ikincisi |
| **layer cache** | Docker'ın değişmeyen adımları yeniden çalıştırmaması. En az değişen dosya en üste kopyalanır |
| **PEP 405** | Sanal ortam standardı. `pyvenv.cfg` dosyasını tanımlar |
| **PEP 735** | `[dependency-groups]` standardı — dev/prod bağımlılık ayrımı |
| **shim** | Gerçek binary'ye yönlendiren küçük ara dosya. Paket yöneticileri `PATH`'e shim koyar |
| **workspace** | Tek repoda birden çok paketin ortak lock ile yönetilmesi (monorepo) |

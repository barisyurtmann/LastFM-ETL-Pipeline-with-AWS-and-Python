# 01 — Sıfırdan Python data projesi iskeleti

**Son doğrulama:** 2026-08-22 (geriye dönük yazıldı — kaynak: ADIM 0 kayıtları, `notes/01–09`)
**Süre:** ~90 dk · **Sıklık:** proje başına bir kez
**Kapsam:** ROADMAP adım **0** (0.1–0.6)

**Bitiş durumu:**

- `git` deposu var, `.gitignore` ve `.gitattributes` **doğrulanmış**
- `pyproject.toml` + `src/` layout kurulu, `import <paket>` çalışıyor
- `uv.lock` var ve commit'lenmiş
- `.env.example` config sözleşmesi olarak yazılmış, `README.md` var

> **Bu runbook mevcut bir repoyu klonlamak için değil** — o [`00`](00-new-machine-setup.md).
> Buradaki adımlar **yeni bir proje** kurarken tekrarlanır.

> **Geriye dönük not:** Bu runbook, iş yapıldıktan haftalar sonra `docs/notes/01–09` ve
> PROGRESS kayıtlarından derlendi. Komutlar ve dosya içerikleri repodaki **gerçek**
> hallerinden alındı; sıra PROGRESS'in adım kayıtlarından çıkarıldı.

---

## Ön koşullar

| Araç | Kurulum | Kontrol |
|---|---|---|
| Git | `winget install --id Git.Git -e` | `git --version` |
| uv | `winget install --id=astral-sh.uv -e` | `uv --version` |

> **`pip install uv` kullanma.** Aracı, yönetmesi gereken şeye (Python'a) bağımlı yapar.
> Kurulumdan sonra terminali kapat-aç.

---

## Bölüm 1 — Depoyu başlat ve `.gitignore` yaz

```bash
mkdir <proje-adı> && cd <proje-adı>
git init
```

`.gitignore`'ı **ilk** yaz. Sebep: sanal ortam veya `.env` bir kez commit'lenirse git
geçmişinden çıkarmak ayrı bir iştir; hiç girmemesi bedavadır.

Bu projenin `.gitignore`'ı:

```gitignore
# --- Python build artifacts ---
# compiled bytecode, regenerated on every run
__pycache__/
# matches .pyc, .pyo, .pyd
*.py[cod]
# package metadata produced by an editable install
*.egg-info/

# --- Virtual environment ---
# machine-specific; recreated from pyproject.toml
.venv/

# --- Tooling caches ---
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage

# --- Secrets ---
# .env holds the Last.fm API key. Never commit it.
# .env.example is committed as a template so a new dev knows what to fill in.
.env
.env.*
!.env.example

# --- Local data lake ---
# Git versions code, not data. Raw JSON and Parquet live outside version control.
/data/

# --- Logs ---
*.log
logs/

# --- OS ---
.DS_Store
```

> **Tuzak — satır sonu yorumu.** `__pycache__/   # comment` yazarsan git **satırın tamamını**
> pattern sayar ve hiçbir şey eşleşmez. Bu projede yaşandı: `.venv/` diske düştüğünde
> `git status` üç kirli girdi gösterdi. Yorum kendi satırında durur.

> **Tuzak — dar pattern yaz.** `/data/` yerine `data` yazarsan, ileride açılacak bir
> `src/<paket>/data/` modülü de sessizce yok sayılır. Baştaki `/` "sadece kökte" demektir.

**Doğrulama — her pattern için ayrı ayrı, örnek üzerinden değil:**

```bash
git check-ignore -v -n .venv/pyvenv.cfg src/<paket>/__init__.py
git status --short --ignored
```

`check-ignore -v` çıktısı `<dosya>:<satır>:<pattern>	<yol>` biçimindedir. Eşleşmeyen yol
için `::	<yol>` görürsün.

> **Tuzak — `check-ignore` "ignore'lu" demez.** `.env.example` için `-v` bir eşleşme
> gösterir ve exit code 0 döner; dosya negation (`!.env.example`) sayesinde aslında
> **takip edilir**. Gerçek soruyu şu cevaplar:
> ```bash
> git add -n .env.example     # "add '.env.example'" derse ignore'lu DEĞİL
> ```

**İlk commit — sadece `.gitignore`:**

```bash
git add .gitignore
git status
git commit -m "chore: add .gitignore"
```

```bash
git log --oneline        # tek commit
git show --stat HEAD     # 1 file changed
```

Neden yalnız: ilk commit'e her şeyi atmak, hangi dosyanın neden eklendiğini geri
izlenemez hale getirir. Commit atomik olur — tek bir amaç taşır.

---

## Bölüm 2 — Satır sonlarını sabitle (`.gitattributes`)

Windows'ta çalışıyorsan bu adım **şart**. Yoksa her dosya CRLF ile yazılır, diff'ler
okunamaz hale gelir ve iki makine arasında sonsuz sahte değişiklik üretilir.

`.gitattributes`:

```gitattributes
# Normalize all text files to LF in the repository and on disk.
# Without this, the Windows machine rewrites every file with CRLF and
# every diff becomes unreadable. Overrides per-machine core.autocrlf.
* text=auto eol=lf

# Binary files must never be touched by the eol filter.
*.parquet binary
*.png     binary
```

Uygulamak için **dört komut**, sırayla:

```bash
git add .gitattributes
git commit -m "chore: enforce LF line endings via .gitattributes"
git add --renormalize .
git rm -r --cached . >/dev/null && git reset --hard
```

> **Tuzak — `--renormalize` yetmez.** Üçüncü komuttan sonra `git status` temiz görünür ama
> **disk hâlâ CRLF'tir**; `--renormalize` yalnız index'i düzeltir. Dördüncü komut dosyaları
> diske yeniden yazar. Bu projede tam olarak bu yaşandı.

**Doğrulama:**

```bash
git ls-files --eol docs/PROGRESS.md
```

Beklenen — **üçü de `lf`**:

```
i/lf    w/lf    attr/text=auto eol=lf   docs/PROGRESS.md
```

`i/` = index (git'in içi), `w/` = working tree (disk), `attr/` = uygulanan kural.

---

## Bölüm 3 — `pyproject.toml` ve `src/` layout

**`uv init` kullanılmadı** — bilinçli. Üretilen bir dosyayı okumakla, dosyayı yazmak farklı
şeyler öğretir. Elle yaz:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "lastfm-etl"
version = "0.1.0"
description = "ETL pipeline for Last.fm listening history"
# Pinned to the minor version of the AWS Lambda python3.14 runtime. Compiled wheels
# (pandas, pyarrow) are built per minor version, so a layer built on 3.15 would fail
# to import on a 3.14 runtime. The upper bound is the deployment target, not a preference.
requires-python = ">=3.14,<3.15"
dependencies = [
    "python-dotenv>=1.2.3",
]

[tool.setuptools.packages.find]
where = ["src"]
```

Klasörü aç:

```bash
mkdir -p src/lastfm_etl
touch src/lastfm_etl/__init__.py
```

| Karar | Sebep |
|---|---|
| Dağıtım adı `lastfm-etl` (**tire**), import adı `lastfm_etl` (**alt çizgi**) | Python tanımlayıcısında tire olamaz — `import lastfm-etl` `SyntaxError` verir. Bu projede `src/lastfm-pipeline/` açılıp sonra silindi |
| `src/` layout | Kurulmamış paket import edilemez. Kurulum bozuksa **test anında** patlar, prod'da değil |
| `requires-python` **üst sınırlı** | Derlenmiş wheel'ler minor sürüme bağlıdır. Deploy hedefi neyse aralık odur |
| Boş alt klasörler (`extract/`, `transform/`) **açılmadı** | Gerçek veriyi görmeden modül sınırı çizmek tahmindir. Klasörler ihtiyaç doğunca açılır |

> **Junior tuzağı:** İlk gün `extract/ transform/ load/ utils/` klasörlerini açmak. Boş
> klasör yapısı proje ilerlemesi gibi görünür ama hiçbir karar içermez — ve yanlış çıktığında
> sökmek, hiç açmamaktan pahalıdır.

---

## Bölüm 4 — Ortamı kur

```bash
uv sync
```

Bu tek komut: `.venv/` oluşturur, bağımlılıkları çözer, `uv.lock` yazar, projeyi editable
kurar.

> **`uv venv` + `uv pip install -e .` kullanma.** O ikili "pip mode"dur ve `uv.lock`'a
> bakmaz. Project mode (`uv sync` / `uv add`) lock dosyasını otoritedir sayar.

**Doğrulama:**

```bash
uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"
```

Beklenen: **`src\lastfm_etl\__init__.py`** ile biten bir yol — `site-packages` **altında değil.**
Editable install'ın anlamı budur: kurulu paket, kaynak dizinini gösterir.

Karşı-kanıt (src layout'un neden işe yaradığı):

```bash
python -c "import lastfm_etl"     # kurulum olmadan → ModuleNotFoundError
```

**Commit:**

```bash
git add pyproject.toml uv.lock src/
git commit -m "build: lock the environment with uv sync"
```

`uv.lock` **commit'lenir** — iki makinenin aynı sürümleri kurmasının tek garantisi odur.

| `uv` komutu | Ne yapar | Klasik karşılığı |
|---|---|---|
| `uv sync` | Lock'tan ortamı **eşitler**, fazlalıkları siler | `pip install -r requirements.txt` (silmez) |
| `uv sync --frozen` | Lock'u güncellemeden kurar, uyumsuzsa patlar (CI) | — |
| `uv add <paket>` | `pyproject.toml` + lock + kurulum, üçü birden | Elle toml + `pip install` |
| `uv add --dev pytest` | Dev bağımlılığı | `requirements-dev.txt` |
| `uv remove <paket>` | Üçünden de siler (transitive dahil) | `pip uninstall` (öksüz bırakır) |
| `uv lock` | Sadece çözer ve yazar — **ortama dokunmaz** | `pip-compile` |
| `uv run <komut>` | Ortamı hazırlar, `activate` gerekmez | `source .venv/bin/activate` + komut |

---

## Bölüm 5 — `.env.example` ve `README.md`

`.env.example` bir örnek değil, **config sözleşmesidir**: pipeline'ın okuduğu her değişken
burada listelenir, böylece yabancı biri kaynağı okumadan projeyi çalıştırabilir.

```
# Last.fm API credentials.
# Get a key at: https://www.last.fm/api/account/create
#
# Copy this file to .env and fill in the value. .env is git-ignored; this file is not.
# This file is the config contract: every variable the pipeline reads is listed here,
# so a stranger can run the project without reading the source.
#
# Format rules (three ways a .env file silently breaks):
#   * No spaces around "=". Some parsers keep the space as part of the value.
#   * No quotes. Some parsers keep them, so "abc" becomes the five-character string "abc".
#   * Comments start with "#" at the beginning of a line. Trailing comments are not portable.
#
# The value is left empty on purpose. Writing LASTFM_API_KEY=your_key_here would let a
# forgotten placeholder reach the API and come back as an opaque authentication error.
# An empty value fails immediately in load_config() (step P1.1) with a message that says
# what to do. Both conventions are common; this project prefers the loud one.
LASTFM_API_KEY=
```

> **Değer boş bırakılır, `your_key_here` yazılmaz.** Unutulmuş bir yer tutucu API'ye gider
> ve anlaşılmaz bir kimlik hatası olarak geri döner. Boş değer **hemen**, ne yapılacağını
> söyleyen bir mesajla patlar.

`README.md` en az şunları içerir: proje ne yapıyor, kurulum komutları (kopyala-yapıştır
çalışan), `.env` nasıl doldurulur, doğrulama komutu, doküman haritası.

**Doğrulama:** README'deki komutları **temiz bir dizinde** baştan çalıştır. Çalışmıyorsa
README yanlıştır — hafızandan yazdığın adımlar eksiktir.

---

## Bütünsel doğrulama

```bash
git status --short                                               # boş
git log --oneline                                                # atomik commit'ler
git ls-files --eol .gitignore                                    # i/lf w/lf
git check-ignore -v .venv/pyvenv.cfg                             # eşleşiyor
git add -n .env.example                                          # add '.env.example'
uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)" # src\... 
```

---

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `.gitignore` hiçbir şeyi yakalamıyor | Satır sonu yorumu pattern'e karışmış | Yorumu ayrı satıra al, `git check-ignore -v` ile **her** pattern'i dene |
| `git status` sürekli kirli | `.gitattributes` sonrası disk yeniden yazılmadı | `git rm -r --cached . && git reset --hard` |
| `ModuleNotFoundError` | `uv sync` yapılmadı ya da `uv run` kullanılmıyor | `uv sync`; komutları `uv run` ile çalıştır |
| `import` `site-packages`'ı gösteriyor | Editable değil, normal kurulum yapılmış | `uv sync` (project mode) |
| `SyntaxError` import satırında | Paket klasör adında tire var | Klasörü alt çizgiyle yeniden adlandır |
| Kurulan sürüm lock'takinden farklı | `uv pip install` kullanılmış | `uv add` / `uv sync` |

---

## Geri alma

| Durum | Ne yapılır |
|---|---|
| `.venv` bozuldu | `rm -rf .venv && uv sync` — asla elle onarma |
| Yanlış paket adı seçildi | Klasörü yeniden adlandır, `pyproject.toml`'daki `name`'i düzelt, `uv sync` |
| `.env` yanlışlıkla commit'lendi | **Önce key'i iptal et/yenile**, sonra geçmişten temizle. Sıra bu — geçmişi temizlemek sızmış anahtarı geçersiz kılmaz |

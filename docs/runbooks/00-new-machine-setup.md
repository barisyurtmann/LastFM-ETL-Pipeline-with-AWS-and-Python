# 00 — Yeni makinede projeyi çalışır hale getirme

**Son doğrulama:** 2026-08-22 · **Süre:** ~15 dk · **Sıklık:** her yeni makinede
**Kapsam:** Repo zaten var (GitHub'da). Bu runbook onu bir bilgisayarda çalışır hale getirir.

**Bitiş durumu:**

- Repo klonlanmış, `git status` **temiz**
- `.venv/` kurulu, `import lastfm_etl` çalışıyor
- `.env` dolu, `load_config()` gerçek key'i okuyor ve maskeli basıyor
- `aws sts get-caller-identity` doğru kimliği dönüyor

> **Sıfırdan repo kuruyorsan** bu değil, [`01`](01-repo-scaffold.md).
> **Bu projeyi ilk kez kuruyorsan** sırayla: bu runbook → [`02`](02-lastfm-api-access.md) (key
> yoksa) → [`03`](03-aws-account-bootstrap.md) (AWS hesabı yoksa).

---

## Ön koşullar

| Araç | Kurulum (Windows) | Kontrol |
|---|---|---|
| Git | `winget install --id Git.Git -e` | `git --version` |
| **uv** | `winget install --id=astral-sh.uv -e` | `uv --version` |
| AWS CLI | `winget install --id Amazon.AWSCLI -e` | `aws --version` |

macOS/Linux: `brew install git uv awscli` ya da
`curl -LsSf https://astral.sh/uv/install.sh | sh`

> **Her kurulumdan sonra terminali kapat-aç.** `PATH` değişkeni süreç başlarken bir kez
> okunur; açık terminal yeni binary'yi göremez. "Kurdum ama `command not found`" diyorsan
> sebebi bu, kurulumu tekrarlama.

> **Python'ı ayrıca kurmana gerek yok.** `uv sync`, `pyproject.toml`'daki
> `requires-python = ">=3.14,<3.15"` aralığına uyan bir yorumlayıcı yoksa kendisi indirir.

---

## Bölüm 1 — Klonla

```bash
git clone <repo-url>
cd LastFM-ETL-Pipeline-with-AWS-and-Python
```

**Doğrulama:**

```bash
git status --short
```

**Çıktı boş olmalı.** Kirliyse → Sorun giderme, "klonladım ama kirli".

---

## Bölüm 2 — Ortamı kur

```bash
uv sync
```

Tek komut üç iş yapar: `.venv/` oluşturur, `uv.lock`'taki **tam sürümleri** kurar, projeyi
editable modda kurar (`src/` importlanabilir hale gelir).

> **`uv pip install -e .` yazma.** O pip uyumluluk katmanıdır ve `uv.lock`'a hiç bakmaz —
> kurduğun sürüm lock'takinden farklı olabilir. Lock dosyasının varlık sebebi tam olarak
> bunu engellemek.

**Doğrulama:**

```bash
uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"
```

Beklenen: yol **`src\lastfm_etl\__init__.py`** ile bitmeli. `site-packages` altında bir yol
görüyorsan editable install olmamış demektir.

---

## Bölüm 3 — `.env` oluştur

`.env` **git'e girmez** — her makinede elle oluşturulur.

```bash
cp .env.example .env
```

Sonra `.env`'i bir editörle aç ve key'i yaz:

```
LASTFM_API_KEY=<gerçek key>
```

| Kural | Sebep |
|---|---|
| `=` etrafında **boşluk yok** | Bazı ayrıştırıcılar boşluğu değerin parçası sayar |
| **Tırnak yok** | Bazı ayrıştırıcılar tırnağı saklar; `"abc"` beş karakterlik dize olur |
| Yorum satır **başında** | Satır sonu yorumu taşınabilir değil |

Key elinde yoksa → [`02`](02-lastfm-api-access.md).

**Doğrulama:**

```bash
uv run python -c "from lastfm_etl.config import load_config; print(load_config())"
```

Beklenen: `Config(lastfm_api_key='***f29d')` — **son dört karakter dışında maskeli.**
Key tam görünüyorsa `__repr__` maskesi bozulmuş demektir, kod hatasıdır.

```bash
git status --short
```

`.env` **listede görünmemeli.** Görünüyorsa `.gitignore` uygulanmamıştır, commit atma.

---

## Bölüm 4 — AWS kimliği

Bu makinenin kendi access key'i olmalı — anahtar makineler arasında taşınmaz.

Adımlar: [`03` runbook'unun "Yeni makine kısa yolu"](03-aws-account-bootstrap.md#yeni-makine-kısa-yolu) —
özet: IAM'de yeni access key üret (tag: makine adı) → `aws configure` → doğrula.

**Doğrulama:**

```bash
aws sts get-caller-identity
```

`Arn` **`user/lastfm-etl-dev`** ile bitmeli.

---

## Bölüm 5 — Bütünsel doğrulama

Beşi de geçmeli:

```bash
git status --short                                                      # boş
uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"        # src\... ile bitiyor
uv run python -c "from lastfm_etl.config import load_config; print(load_config())"   # maskeli
aws sts get-caller-identity                                             # user/lastfm-etl-dev
git ls-files --eol docs/PROGRESS.md                                     # i/lf w/lf
```

Son komut satır sonlarını kontrol eder. Beklenen:

```
i/lf    w/lf    attr/text=auto eol=lf   docs/PROGRESS.md
```

`w/crlf` görürsen `.gitattributes` bu makinede uygulanmamış — Sorun giderme'ye bak.

---

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `git`/`uv`/`aws: command not found` | `PATH` süreç başında donmuş | Terminali kapat-aç |
| **Klonladım ama `git status` kirli** | `.gitattributes` uygulanmamış, dosyalar CRLF ile yazılmış | `git ls-files --eol` ile teyit et, sonra: `git rm -r --cached . && git reset --hard` |
| `git status` "M" diyor ama `git diff` boş | Bayat stat-cache | `git diff` otoritedir; `git add --renormalize .` ya da yukarıdaki dizi |
| `ModuleNotFoundError: lastfm_etl` | `uv sync` çalıştırılmadı, ya da `uv run` olmadan çağrıldı | `uv sync`; komutları `uv run` ile çalıştır |
| `ConfigError: Missing or empty environment variables` | `.env` yok/boş **ya da** ortamda boş bir `LASTFM_API_KEY` var | `.env`'i doldur. Ortam değişkeni dosyayı **yener**: `unset LASTFM_API_KEY` |
| `.env` `git status`'ta görünüyor | Yanlış dizindesin ya da `.gitignore` bozuk | `git check-ignore -v .env` |
| `aws: InvalidClientTokenId` | Bu makinenin anahtarı silinmiş/yanlış | [`03`](03-aws-account-bootstrap.md) Bölüm 6 |

---

## Geri alma

| Durum | Ne yapılır |
|---|---|
| Ortam bozuldu | `rm -rf .venv && uv sync` — `.venv` her zaman yeniden üretilebilir, asla elle düzeltilmez |
| Lock ile ortam uyuşmuyor | `uv sync --frozen` — lock'u güncellemeden kurar, uyumsuzsa patlar |
| Yanlış dosyalar commit'lendi | Commit'i geri al; `.gitignore`'ı `git check-ignore -v` ile doğrula |

---

## Günlük akış

```
git pull  →  uv sync  →  <çalış>  →  uv add X (gerekirse)  →  git add uv.lock  →  commit  →  git push
```

`git pull` sonrası `uv sync` alışkanlık olmalı: başkası (ya da diğer makinen) bağımlılık
eklediyse lock değişmiştir ve ortamın geridedir.

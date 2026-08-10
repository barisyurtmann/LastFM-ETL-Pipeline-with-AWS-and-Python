# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-10 (ev bilgisayarı)
**Current step:** 0 — Repo setup ([plan](ROADMAP.md#adım-0--repo-kurulumu))
**Next sub-step:** 0.6 — Adım 0 kapanış commit'i

**Sıradaki oturumda ilk iş:**
> `git pull`, sonra `uv sync` (ortam `.gitignore`'lu, her makinede yeniden kurulur).
> `uv run python -c "import lastfm_etl"` sessizce geçmeli.
>
> Sonra 0.6: Adım 0'ın bitti tanımı ([ROADMAP](ROADMAP.md#adım-0--repo-kurulumu))
> madde madde gözden geçirilecek. Açık kalan tek madde: *"README bir yabancının
> repoyu klonlayıp çalıştırmasına yetiyor"* — **yabancı testi** henüz yapılmadı
> (boş klasörde `git clone` → README'yi sıfırdan takip et). Detay: `docs/notes/10` §11.

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

## Açık sorular

- Build backend `setuptools` seçildi; `uv` bir build backend değil (resolver + paket
  yöneticisi), dolayısıyla ADR-0003 bu kararı değiştirmiyor. `hatchling` alternatifi
  açık kalmaya devam ediyor; değişirse ADR yazılır.
- `.python-version` yok. `requires-python = ">=3.11"` bir aralık — iki makinede farklı
  yorumlayıcı seçilebilir (ev: 3.14.5). Sapma görülürse `uv python install` +
  `.python-version` ile sabitlenecek. Şimdilik bilinçli olarak eklenmedi.
- Adım 8.5'te CI'da `uv`'nin **kendi sürümü** sabitlenecek. Bağımlılıkları kilitleyip
  aracı kilitlememek, "kendiliğinden bozulan build" riskini açık bırakır.

## Git geçmişinde görünmeyen kararlar

- Veri gölü `/data/` altında yaşar ve gitignore'ludur. Klasör yapısı ileride kurulacak
  S3 yapısını (`raw/`, `curated/`) birebir taklit eder — böylece AWS'ye taşırken yol
  mantığı değişmez.
- `docs/notes/` Türkçe (öğrenme defteri), `docs/adr/` İngilizce (portfolyo çıktısı).
- `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı. Tek kaynak burasıdır.

## Sonraki oturum için hatırlatma

- Oturuma `git pull` ile başla, `git push` ile bitir. İki makinede çalışılıyor.
- İş makinesinde ilk `git pull`'dan sonra `git status` **temiz** olmalı. Kirliyse
  `.gitattributes` orada uygulanmamış demektir — `git ls-files --eol` ile bak.

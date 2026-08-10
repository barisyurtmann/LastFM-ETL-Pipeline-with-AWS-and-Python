# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-10 (iş bilgisayarı)
**Current step:** 0 — Repo setup ([plan](ROADMAP.md#adım-0--repo-kurulumu))
**Next sub-step:** 0.4 — Sanal ortam. **Karar verildi (uv), uygulanmadı.**

**Sıradaki oturumda ilk iş — ev bilgisayarı:**
> `git pull` (3 commit bekliyor), sonra sırayla:
>
> 1. **Gözlem — 5 dakika, commit yok.** `python -m venv .venv-test` çalıştır,
>    `.venv-test/pyvenv.cfg` dosyasını aç ve oku (`home`, `include-system-site-packages`),
>    `.venv-test/Scripts/` içine bak. Sonra klasörü sil. Amaç: `uv`'nin senin yerine
>    ne ürettiğini önce elle görmek. Detay: `docs/notes/08-virtual-environments-and-uv.md` §2
> 2. `uv` kurulumu (Windows: `winget install --id=astral-sh.uv` veya resmî installer).
>    `uv --version` ile doğrula
> 3. `uv venv` → `.venv/` oluşacak
> 4. `git status` **temiz kalmalı**. Kirliyse `.gitignore` düzeltmesi (`6c778fc`) o makinede
>    uygulanmamış demektir
> 5. `uv pip install -e .`
> 6. **0.3'ün devredilmiş doğrulaması:**
>    `uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"`
>    Çıktı `src/lastfm_etl/__init__.py` yolunu göstermeli — `site-packages` altını
>    **değil**. Gösterirse editable install çalışmamış demektir.
>    Bu çalışmadan 0.3 gerçekten bitmiş sayılmaz.
>
> Sonra `uv.lock` üretimi ve 0.4 kapanış commit'i konuşulacak.

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
      **Karar verildi ama uygulanmadı** — kurulum ev makinesinde yapılacak.

## Açık sorular

- Build backend `setuptools` seçildi; `uv` bir build backend değil (resolver + paket
  yöneticisi), dolayısıyla ADR-0003 bu kararı değiştirmiyor. `hatchling` alternatifi
  açık kalmaya devam ediyor; değişirse ADR yazılır.
- `uv.lock` üretimi 0.4'ün son parçası. `dependencies = []` iken lock dosyasının anlamı
  ne olur — ev oturumunda konuşulacak.

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

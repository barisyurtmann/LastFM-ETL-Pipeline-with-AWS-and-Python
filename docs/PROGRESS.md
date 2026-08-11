# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-11 (iş bilgisayarı)
**Current step:** 1 — Veriyi tanı ([plan](ROADMAP.md#adım-1--veriyi-tanı))
**Next sub-step:** 1.3 — Bozuk `api_key` ile çağır, HTTP 200 + gövdede `error` davranışını gör

> **ADIM 0 TAMAMLANDI.** Bitti tanımının beş maddesi de doğrulandı (aşağıda).
> **1.1 ve 1.2 TAMAMLANDI.**

**1.3'ün hazırlığı:** ortam ve çağrı biçimi hazır. Aynı `curl.exe` komutu, tek fark
`api_key` değerinin bilinçli olarak bozulması. Beklenti (henüz **doğrulanmadı**):
HTTP `200` + gövdede `{"error": 10, "message": "Invalid API key..."}`.
Bu payload da 1.4'te diske kaydedilecek — hata payload'ı başarı payload'ı kadar değerli.

**Adım 1 hatırlatması:** bu adımın çıktısı kod değil, **bilgi ve örnek dosya**. Kod yazma
isteği gelirse Adım 3'e aittir.

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
- `git pull` sonrası `git status` **temiz** olmalı. Kirliyse `.gitattributes` o makinede
  uygulanmamış demektir — `git ls-files --eol` ile bak.
- **`uv` her iki makinede de kurulu** (ev + iş). Yeni bir makinede `uv sync` şart.
- **`.env` git'e girmez** — her makinede elle oluşturulur. Yeni makinede ilk iş:
  `.env.example`'ı kopyalayıp gerçek key'i yazmak.
- `curl` çağrılarından önce `.env`'i oturuma yükle (`docs/notes/11` §3). Sır komut
  satırına elle yazılmaz.
- Adım 1 kod adımı **değil**. Çıktısı: kaydedilmiş gerçek payload + hata payload'ı +
  grain cümlesi + hedef şema tablosu. Kod yazma isteği gelirse Adım 3'e ait demektir.

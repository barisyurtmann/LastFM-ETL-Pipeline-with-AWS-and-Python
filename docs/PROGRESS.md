# Progress

Bu dosya projenin **tek durum kaynağıdır**. Her oturumun başında okunur, her alt adımın
sonunda güncellenir.

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-07
**Current step:** 0 — Repo setup
**Next sub-step:** 0.3 — `pyproject.toml` + `src/` layout

---

## Adım 0 alt adımları

| # | Alt adım | Durum |
|---|---|---|
| 0.1 | `.gitignore` | ✅ bitti |
| 0.2 | İlk commit | ✅ bitti |
| 0.3 | `pyproject.toml` + `src/` layout | ⬜ sıradaki |
| 0.4 | Sanal ortam (`uv` / `venv`) | ⬜ |
| 0.5 | `README.md` + `.env.example` | ⬜ |
| 0.6 | Adım 0 kapanış commit'i | ⬜ |

## Tamamlananlar

- [x] **0.1** `.gitignore` yazıldı ve `git check-ignore -v` ile doğrulandı.
      Kritik kontrol: `src/lastfm_etl/raw` **eşleşmedi** — kalıplar yeterince dar yazılmış.
- [x] **0.2** İlk commit atıldı: `chore: add .gitignore`
- [x] `docs/` yapısı kuruldu (PROGRESS, ADR, notes)

## Açık sorular

- `uv` mi `venv` + `pip` mi? — 0.4'te karara bağlanacak, ADR yazılacak.
- Paket adı ne olacak (`lastfm_etl`?) — 0.3'te karara bağlanacak.

## Git geçmişinde görünmeyen kararlar

- Veri gölü `/data/` altında yaşar ve gitignore'ludur. Klasör yapısı ileride kurulacak
  S3 yapısını (`raw/`, `curated/`) birebir taklit eder — böylece AWS'ye taşırken yol
  mantığı değişmez.
- `docs/notes/` Türkçe (öğrenme defteri), `docs/adr/` İngilizce (portfolyo çıktısı).
- `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı. Tek kaynak burasıdır.

## Sonraki oturum için hatırlatma

- Oturuma `git pull` ile başla, `git push` ile bitir. İki makinede çalışılıyor.

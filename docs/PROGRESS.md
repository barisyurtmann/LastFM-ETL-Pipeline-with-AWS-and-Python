# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-07 (iş bilgisayarı — eve devam edilecek)
**Current step:** 0 — Repo setup ([plan](ROADMAP.md#adım-0--repo-kurulumu))
**Next sub-step:** 0.3 — `pyproject.toml` + `src/` layout

**Sıradaki oturumda cevaplanacak açık soru:**
> Kodu neden `src/` klasörünün içine koyuyoruz? Repo kökünde `lastfm_etl/` olsa ne
> değişirdi — somut teknik bir sonucu var mı, yoksa sadece düzen meselesi mi?
> (Barış bu soruya cevap vermeden 0.3 anlatılmaya başlanmayacak.)

---

## Tamamlananlar

- [x] **0.1** `.gitignore` yazıldı ve `git check-ignore -v` ile doğrulandı.
      Kritik kontrol: `src/lastfm_etl/raw` **eşleşmedi** — kalıplar yeterince dar yazılmış.
- [x] **0.2** İlk commit atıldı: `chore: add .gitignore`
- [x] `docs/` yapısı kuruldu (PROGRESS, ADR, notes) — `docs: add project documentation structure`
      ADR-0001 yazıldı, `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı,
      custom instructions yenilendi.

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

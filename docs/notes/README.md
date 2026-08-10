# Öğrenme Notları

Bu klasör, proje boyunca öğrenilen **genel** bilgileri tutar. Türkçe yazılır.

## `notes/` mi `adr/` mi?

Testi tek soru: **"Bu bilgi başka bir projede de geçerli mi?"**

| Cevap | Nereye |
|---|---|
| Evet — genel bilgi (`.gitignore` syntax'ı, commit mesajı formatı) | `notes/` |
| Hayır — bu projeye özel karar (neden Parquet, neden bu partition şeması) | `adr/` |

## İçindekiler

| # | Konu | Adım |
|---|---|---|
| [01](01-git-and-gitignore.md) | Git temelleri ve `.gitignore` | 0.1 |
| [02](02-commit-conventions.md) | Commit mesajları ve ilk commit | 0.2 |
| [03](03-line-endings.md) | Satır sonları (CRLF/LF) ve `.gitattributes` | 0.2–0.3 arası |
| [04](04-src-layout-and-syspath.md) | `src/` layout ve `sys.path` | 0.3 |
| [05](05-toml-and-pyproject.md) | TOML formatı ve `pyproject.toml` anatomisi | 0.3 |
| [06](06-modules-packages-and-init.md) | Modül, paket, `__init__.py` ve isimlendirme | 0.3 |
| [07](07-staging-area-and-atomic-commits.md) | Staging area, `git diff --staged`, atomik commit | 0.4 |
| [08](08-virtual-environments-and-uv.md) | Sanal ortamlar, editable install, lock dosyası, `uv` (kavramlar) | 0.4 |
| [09](09-uv-workflows-and-classic-equivalents.md) | `uv` iş akışları, komut referansı, `uv`'siz karşılıkları | 0.4 |
| [10](10-writing-a-readme.md) | README yazmak: okuyucular, bölümler, test etme, anti-pattern'lar | 0.5 |

---

Yeni not eklerken bu tabloyu güncelle. Index'i olmayan not klasörü, altı ay sonra
kimsenin bakmadığı bir klasördür.

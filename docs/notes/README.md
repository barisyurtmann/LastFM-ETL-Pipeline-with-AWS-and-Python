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

---

Yeni not eklerken bu tabloyu güncelle. Index'i olmayan not klasörü, altı ay sonra
kimsenin bakmadığı bir klasördür.

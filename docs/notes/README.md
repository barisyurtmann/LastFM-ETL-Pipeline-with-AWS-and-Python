# Öğrenme Notları

Bu klasör, proje boyunca öğrenilen **genel** bilgileri tutar. Türkçe yazılır.

## `notes/` mi `adr/` mi?

Testi tek soru: **"Bu bilgi başka bir projede de geçerli mi?"**

| Cevap | Nereye |
|---|---|
| Evet — genel bilgi (`.gitignore` syntax'ı, commit mesajı formatı) | `notes/` |
| Hayır — bu projeye özel karar (neden Parquet, neden bu partition şeması) | `adr/` |

## Not şablonu — 20'den sonraki her not

Her not **en fazla ~60 satır** ve hep aynı beş bölüm:

```markdown
# 20 — Başlık

> **Kısa cevap** — <notun cevapladığı soru>
>
> 1. <en kritik sonuç>
> 2. <ikinci>
> 3. <üçüncü>

## Neden
<max 10 satır. Bu bilinmezse ne kırılır.>

## Nasıl
<komut veya kod, gerektiği kadar>

## Kanıt
<çalıştırılıp doğrulanacak komut ve beklenen çıktı>

## Mülakat cevabı
<soru + karar → gerekçe → trade-off sırasıyla üç-dört cümle. Karar yoksa "—">
```

Sınır bir kalite kuralı değil, bir **öncelik zorlayıcısıdır**: sınır yokken her şey içeri
girer ve 400 satırlık bir not bir daha hiç açılmaz. Konu 60 satıra sığmıyorsa ya ikiye
bölünür ya da satır satır anlatım [`docs/annotated/`](../annotated/README.md)'a gider.

**Mülakat cevabı bölümü** notun tek *sözlü* çıktısıdır. Bir konuyu bilmek ile onu 30
saniyede gerekçesiyle savunabilmek ayrı becerilerdir; ikincisi yazılmadığı sürece gelişmez.

Format: bir soru, ardından **karar → gerekçe → trade-off**. "Şunu kullandık" bir cevap
değildir — cevap, alternatifi neden elediğini ve **hangi koşulda başka seçeceğini** içerir.
Son cümle genellikle en değerlisidir: kararın sınırını bilmek, kararı bilmekten zordur.

**Her notta olmak zorunda değil.** Saf referans notlarında (komut listeleri, syntax)
savunulacak bir karar yoktur; bölüm `—` ile geçilir. Uydurulmuş bir mülakat sorusu,
doldurulmuş bir alandan başka bir şey değildir.

**01–19 arası notlar bu şablondan önce yazıldı.** Onlar budanmadı; her birinin başına
aynı "Kısa cevap" bloğu eklendi. Blok yetiyorsa gerisini okumana gerek yok.
`Mülakat cevabı` bloğu eski notlara **toplu olarak** eklenmez — konu iş sırasında
tekrar karşımıza çıktığında o notun bloğu yazılır. Geriye dönük toplu doldurma,
hatırlanmayan kararlar için uydurma cevap üretir.

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
| [11](11-manual-api-calls-and-auth-models.md) | API'yi elle çağırmak, `.env` yükleme, regex, auth modelleri kataloğu | 1.2 |
| [12](12-shell-basics.md) | Shell temelleri: operatörler, exit code, `export`/`source`, bash ↔ PowerShell | 1.4 |
| [13](13-data-source-discovery.md) | Yeni veri kaynağı keşif protokolü: altı boyut, örnekleme, null'ın yüzleri | 1.5 |
| [14](14-grain-and-fact-tables.md) | Grain belirleme protokolü, fact table türleri, anahtar seçimi, mixed grain | 1.6 |
| [15](15-schema-design-and-field-elimination.md) | Şema tasarımı: alan eleme (4 sınav), null'ın yedi kılığı, tip seçimi, isimlendirme, ordinal materyalizasyonu | 1.7 |
| [16](16-shell-loops-and-measurement.md) | Shell'de döngü (`for`/`while`, form seçimi, PowerShell), `curl -w` ile ölçüm, gecikme istatistikleri, ölçüm araçları | 1.8 |
| [17](17-rate-limits-discovery-and-backoff.md) | Rate limit: dört aşamalı keşif protokolü (bash), header standartları, limit algoritmaları, üstel backoff + jitter, retry taksonomisi | 1.8 |
| [18](18-config-secrets-and-fail-fast.md) | Config vs sabit ayrımı, `.env` tehdit modeli, fail-fast, maskeli `__repr__`, `dataclass` vs `pydantic-settings`, `python-dotenv` öncelik sırası | P1.1 |
| [19](19-python-language-tools-in-config-py.md) | Python dil araçları: hızlı referans tablosu, iddiaları doğrulayan kanıt komutları, yanlış anlaşılan noktalar. Satır satır anlatım için → `docs/annotated/` | P1.1 |
| [20](20-aws-sdk-and-boto3.md) | AWS bir API'dir: konsol/CLI/SDK kardeşliği, `boto3` ne yapıyor, SigV4 imzalama, `client` vs `resource`, `Session` | P1.2 |
| [21](21-aws-credentials-and-the-credential-chain.md) | IAM kavram haritası, access key anatomisi ve kuralları, `~/.aws` iki dosya ayrımı, **credential chain**, güvenlik yapılmayacaklar listesi | P1.2 |
| [22](22-packages-init-and-public-api.md) | Modül vs paket, `__init__.py`'nin dört işi, re-export ve kapsülleme, **exception'ların neden arayüzün parçası olduğu**, `__all__`, cold start maliyeti | P2.1 |
| [23](23-pagination-and-loop-termination.md) | Sayfalama: durma koşulları (sayım vs aritmetik), sonsuz döngü koruması, `for`/`else`, sayfa tavanı, sayfa boyutu seçimi | P2.1 |
| [24](24-generators-and-yield.md) | Generator ve `yield`, tembel değerlendirme, `list` vs `Iterator` trade-off'u, tek kullanımlık olma tuzağı | P2.1 |
| [25](25-reading-untrusted-json.md) | Dış dünyadan gelen JSON: `.get()` vs `[]`, tip kapısı, "yok"un kılıkları, sentinel isimlendirme, dar `try`, dedup için `set`/`setdefault` | P2.2 |
| [26](26-etl-vs-elt.md) | ETL vs ELT, medallion katmanları, ham katmanın bedeli, hangi koşulda hangisi | P2.2 |

## Prosedürler

Bu klasör **ne** ve **neden**'i tutar; **nasıl yapılır**'ı değil. Bir işi baştan tekrar
etmen gerekiyorsa (AWS hesabı kurmak, yeni makineye geçmek) → [`docs/runbooks/`](../runbooks/README.md).

Testi: *"Bu bir bilgi mi, bir eylem dizisi mi?"* Bilgiyse buraya, eylem dizisiyse runbook'a.

## Kodun yorumlu aynası

`src/` altındaki her `.py` dosyasının satır satır Türkçe yorumlanmış kopyası ayrı bir
klasörde durur: [`docs/annotated/`](../annotated/README.md). Bir **satırın** ne yaptığını
öğrenmek istiyorsan oraya bak; bir **konuyu** öğrenmek istiyorsan buraya.

---

Yeni not eklerken bu tabloyu güncelle. Index'i olmayan not klasörü, altı ay sonra
kimsenin bakmadığı bir klasördür.

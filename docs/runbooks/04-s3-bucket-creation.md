# 04 — S3 bucket oluşturma

**Son doğrulama:** 2026-08-22 · **Süre:** ~15 dk · **Sıklık:** ortam başına bir kez
**Kapsam:** ROADMAP adım **P1.3**

**Bitiş durumu:**

- İki bucket var: `lastfm-etl-raw-<ek>` ve `lastfm-etl-transformed-<ek>`
- İkisi de `eu-central-1`, versioning açık, public erişime tamamen kapalı
- İkisinde de `Project=lastfm-etl` tag'i
- **Hiç klasör oluşturulmadı** — key şeması kararlaştırıldı, yaratılmadı

> Kararların gerekçesi: [ADR-0011](../adr/0011-deploy-all-resources-in-eu-central-1.md)
> (bölge) ve [ADR-0012](../adr/0012-separate-raw-and-transformed-data-into-two-buckets.md)
> (iki bucket). Bu runbook **nasıl**'ı anlatır, **neden**'i orada.

---

## Ön koşullar

- [`03`](03-aws-account-bootstrap.md) tamamlanmış: `aws sts get-caller-identity` çalışıyor
- Konsolda sağ üstteki bölge seçicisi **eu-central-1 (Frankfurt)**

---

## Bölüm 0 — İsmi önceden seç

Bucket adı **oluşturulduktan sonra değişmez** ve silinen ad güvenilir biçimde geri gelmez —
AWS bucket silmemeyi, boşaltıp tutmayı önerir. İsmi klavyeye gitmeden karar ver.

| Kural | Değer |
|---|---|
| Uzunluk | 3–63 karakter |
| İzinli karakterler | küçük harf, rakam, `-`, `.` |
| Başlangıç/bitiş | harf veya rakam |
| **Nokta kullanma** | Virtual-hosted URL `bucket.s3.<bölge>.amazonaws.com` biçimindedir; TLS wildcard sertifikası **tek seviye** eşleşir. Noktalı ad sertifikayı bozar |
| Ad küresel | Dünyadaki tüm AWS hesaplarıyla aynı havuz. Sonek şart |
| Yasaklı önekler | `xn--`, `sthree-`, `amzn-s3-demo-` |
| Yasaklı sonekler | `-s3alias`, `--ol-s3`, `.mrap`, `--x-s3`, `--table-s3` |

Kalıp: `lastfm-etl-<katman>-<ek>` — `<katman>` = `raw` \| `transformed`.

Sonek seçimi:

| Seçenek | Artı | Eksi |
|---|---|---|
| Hesap numarası | Benzersizlik garantili, hangi hesap belli | Hesap no bucket adında görünür |
| Kısa kişisel ek (`by26`) | Kısa, sızıntı yok | Benzersizlik garanti değil |

---

## Bölüm 1 — `raw` bucket'ı oluştur

1. Konsol → **S3** → **Create bucket**
2. **Bucket type**: `General purpose`
3. **Bucket name**: `lastfm-etl-raw-<ek>`
4. **AWS Region**: sağ üstten `eu-central-1` olduğunu **doğrula**
5. **Object Ownership**: `ACLs disabled (recommended)` — varsayılan, **dokunma**
6. **Block Public Access settings for this bucket**: dört kutu da işaretli — **dokunma**
7. **Bucket Versioning**: **`Enable`** ← varsayılan `Disable`; **değiştirilecek tek ayar**
8. **Tags**: `Project` = `lastfm-etl`
9. **Default encryption**: `SSE-S3` — varsayılan, dokunma
10. **Create bucket**

---

## Bölüm 2 — `transformed` bucket'ı oluştur

Bölüm 1'i `lastfm-etl-transformed-<ek>` adıyla **birebir** tekrarla. Aynı bölge, aynı
ayarlar, aynı tag.

> İki bucket'ın ayarları elle senkron tutuluyor — aralarındaki sapmayı hiçbir şey otomatik
> yakalamıyor. Bölüm 3'teki komutları **ikisi için de** çalıştır; sapmayı yakalayan tek şey
> o kontrol.

---

## Bölüm 3 — Doğrulama

```bash
aws s3 ls
```

İki bucket listelenmeli.

Her bucket için üç komut (`<bucket>` yerine gerçek adı yaz):

```bash
aws s3api get-bucket-location        --bucket <bucket>
aws s3api get-bucket-versioning      --bucket <bucket>
aws s3api get-public-access-block    --bucket <bucket>
```

| Komut | Beklenen |
|---|---|
| `get-bucket-location` | `"LocationConstraint": "eu-central-1"` |
| `get-bucket-versioning` | `"Status": "Enabled"` |
| `get-public-access-block` | Dört alan da `true` |

Tag kontrolü:

```bash
aws s3api get-bucket-tagging --bucket <bucket>
```

Beklenen: `Project` = `lastfm-etl`.

**Kontrol listesi:**

- [ ] İki bucket, ikisi de `eu-central-1`
- [ ] İkisinde versioning `Enabled`
- [ ] İkisinde dört public access bloğu `true`
- [ ] İkisinde `Project=lastfm-etl`
- [ ] Konsolda **hiç klasör oluşturulmadı**

---

## Key şeması — kararlaştırılır, oluşturulmaz

S3'te klasör yoktur. Nesnenin key'i düz bir dizedir; içindeki `/` karakterleri sıradan
karakterlerdir ve konsol onlara bakıp bir ağaç **çizer**. Konsoldaki "Create folder"
butonu adı `/` ile biten **0 byte'lık bir nesne** yaratır — gerçek bir klasör değil.

Kod `to_processed/lastfm_raw_20260822T030000Z.json` key'iyle yazdığı anda ağaç kendiliğinden
görünür. Bu yüzden şema burada **yazılır**, oluşturulmaz:

```
lastfm-etl-raw-<ek>/
    to_processed/lastfm_raw_<ISO8601-UTC>.json     ← extract Lambda buraya yazar
    processed/lastfm_raw_<ISO8601-UTC>.json        ← transform sonrası taşınır

lastfm-etl-transformed-<ek>/
    tracks/
    artists/
```

Zaman damgası: **ISO 8601 basic, UTC** — `20260822T030000Z`.

| Karar | Sebep |
|---|---|
| UTC | Lambda UTC'de çalışır. Yerel saat yazmak, saat değişiminde iki dosyanın çakışması demektir |
| ISO 8601 | **Alfabetik sıra = kronolojik sıra.** S3 listelemesi alfabetiktir; `08/22/2026` bu özelliği kaybeder |
| `Z` soneki | "Bu UTC" der. Sonek yoksa altı ay sonra hangi dilim olduğu bilinemez |

---

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `BucketAlreadyExists` | Ad küresel havuzda alınmış (başka bir hesapta olabilir) | Soneki değiştir. Hata "sende var" demek değildir |
| `BucketAlreadyOwnedByYou` | Ad **senin** hesabında zaten var | `aws s3 ls` ile bak |
| `InvalidBucketName` | Büyük harf, alt çizgi, çift nokta veya yasaklı önek/sonek | Bölüm 0'daki kurallar |
| Bucket yanlış bölgede oluştu | Konsolun bölge seçicisi başka bölgedeydi | Bölge **değiştirilemez**. Yeni bucket aç, eskisini boşalt |
| `get-bucket-location` → `null` | Bu `us-east-1` demektir (tarihsel bir tuhaflık: `us-east-1` için `LocationConstraint` boş döner) | Yanlış bölgedesin — yukarıdaki satır |
| `AccessDenied` | Yanlış kimlikle çağırıyorsun | `aws sts get-caller-identity` |
| Konsolda klasör oluşturuldu | 0 byte'lık sahte nesne yaratıldı | Zararsız ama gereksiz; nesneyi sil |

---

## Geri alma

| Durum | Ne yapılır |
|---|---|
| Yanlış isim/bölge | Bucket'ı boşalt, sonra sil, doğrusunu oluştur. **Aynı adı hemen tekrar kullanamayabilirsin** — silinen ad geç serbest kalır, bazen hiç kalmaz |
| Versioning açılması unutuldu | Sonradan açılabilir: konsolda **Properties → Bucket Versioning → Edit → Enable**. Açılmadan önce yazılmış nesneler `null` versiyon ID'si taşır |
| Versioning yanlışlıkla açıldı | **Kapatılamaz**, yalnız `Suspended` olur; mevcut versiyonlar durur ve faturalanmaya devam eder |
| Bucket'ı silmek gerekiyor | Önce tüm nesneler **ve tüm versiyonlar** silinmeli — versioning açıkken normal silme delete marker bırakır, bucket boş sayılmaz |

---

## Kaynaklar

- [Bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- [Creating a general purpose bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)

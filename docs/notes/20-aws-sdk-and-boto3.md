# 20 — AWS SDK ve `boto3`: AWS ile program olarak konuşmak

> **Kısa cevap** — AWS'ye koddan iş nasıl yaptırılır?
>
> 1. AWS'nin **tamamı** bir HTTPS API'sidir. Konsoldaki her tıklama, her `aws` komutu ve
>    her `boto3` çağrısı aynı API'ye giden bir HTTP isteğine dönüşür. Üçü kardeştir.
> 2. `boto3` = AWS'nin **resmî Python kütüphanesi** (SDK). İşi: isteği kurmak, **imzalamak**,
>    hata olursa tekrar denemek, JSON cevabı Python `dict`'ine çevirmek.
> 3. `boto3.client("s3")` yazarken kimlik bilgisi **vermezsin** — `boto3` onu kendi arar.
>    Nereden aradığı ayrı bir konu → [not 21](21-aws-credentials-and-the-credential-chain.md).

---

## 1. Neden

Konsol tıklaması ölçeklenmez. Pipeline'ın her gece 03:00'te kendi kendine çalışması
gerekiyor ve Lambda'nın içinde tarayıcı yok, fare yok, tıklayacak insan yok. Bir işin
otomatik olması, o işi bir **programın** yapması demektir. Program da AWS ile
konuşabilmek için bir yola muhtaç.

Bu bilinmezse şu olur: insan "AWS = web sitesi" sanır, konsolda yaptığı şeyle koddan
yaptığı şeyin **farklı** olduğunu düşünür, ikisi arasında bağ kuramaz. Oysa aynı şey.

---

## 2. Kavram katmanları

| Katman | Ne | Örnek | Kim çalıştırır |
|---|---|---|---|
| **AWS Service API** | AWS'nin gerçek arayüzü. HTTPS endpoint'leri | `s3.eu-central-1.amazonaws.com` | — |
| **Konsol** | O API'yi çağıran bir web sitesi | Tarayıcıdaki "Create bucket" butonu | İnsan |
| **CLI** | O API'yi çağıran bir terminal aracı | `aws s3 ls` | İnsan (veya script) |
| **SDK** | O API'yi çağıran bir kütüphane | `boto3` (Python), `aws-sdk` (JS), `boto` ≠ | **Kod** |
| **Senin kodun** | SDK'yı çağırır | `src/lastfm_etl/` | Lambda / sen |

> **API** = Application Programming Interface — bir sistemin dışarıya açtığı, program
> tarafından çağrılabilen arayüz.
> **SDK** = Software Development Kit — o API'yi belirli bir dilden kullanmayı kolaylaştıran
> kütüphane paketi.

**Kritik sonuç:** Konsoldan yaptığın hiçbir şey "koddan yapılamayan" bir şey değildir.
Tersi de doğru. Konsolu öğrenme aracı olarak seçtik; API'nin kendisi değişmiyor.

---

## 3. `boto3` ne yapıyor — kutuyu açalım

Sen bunu yazacaksın (P2.2'de):

```python
import boto3

s3 = boto3.client("s3")
s3.put_object(Bucket="lastfm-etl-raw-...", Key="raw/x.json", Body=b"{}")
```

Bu iki satırda `boto3` senin adına şunları yapar:

| Adım | Ne yapıyor | Elle yapsan |
|---|---|---|
| 1 | Kimlik bilgisini bulur (→ not 21) | Dosya okuma, öncelik sırası kodu |
| 2 | Doğru endpoint URL'ini kurar (bölgeye göre) | Bölge → URL eşlemesi tablosu |
| 3 | İsteği **SigV4** ile imzalar | HMAC-SHA256 zinciri, ~40 satır kripto kodu |
| 4 | HTTPS isteğini gönderir | `requests` |
| 5 | 5xx / throttling hatalarında **tekrar dener** (exponential backoff) | Retry döngüsü + jitter (→ not 17) |
| 6 | XML/JSON cevabı Python `dict`'ine çevirir | Ayrıştırma kodu |
| 7 | Hata kodunu Python exception'ına çevirir (`ClientError`) | `if status == 403: ...` |

> **SigV4** (Signature Version 4) = AWS'nin istek imzalama yöntemi. **Secret access key ağ
> üzerinden hiç gönderilmez.** Bunun yerine secret bir anahtar olarak kullanılıp isteğin
> özeti (metot, yol, başlıklar, zaman damgası) imzalanır; AWS aynı hesabı kendi tarafında
> yapıp imzaları karşılaştırır. Bu yüzden imza **zaman damgası** taşır — saatin 5 dakikadan
> fazla kaymışsa istekler reddedilir. ("Kod çalışıyordu, sabah bozuldu" vakalarının bir kısmı budur.)

`boto3`'ün altında **`botocore`** vardır: asıl işi yapan alt katman. `boto3` onun üstündeki
Python dostu kabuk. Hata mesajlarında `botocore.exceptions.ClientError` görürsen şaşırma —
aynı ailedendir.

---

## 4. `client` mi `resource` mı

`boto3`'ün iki arayüzü var. Örneklerde ikisini de görürsün:

| | `boto3.client("s3")` | `boto3.resource("s3")` |
|---|---|---|
| Seviye | Düşük — AWS API metotlarının **birebir** karşılığı | Yüksek — nesne yönelimli sarmalayıcı |
| Örnek | `s3.put_object(Bucket=..., Key=...)` | `bucket = s3.Bucket(...); bucket.upload_file(...)` |
| Kapsam | **Her** servis, **her** metot | Sadece birkaç servis, eksik kapsama |
| Durum | Aktif | **Bakım modu** — AWS 2023'ten beri yeni servis/özellik eklemiyor |

**Biz `client` kullanacağız.** Sebep sadece "AWS öyle diyor" değil: `client` metotları AWS
dokümanındaki API isimleriyle **aynı**. `put_object` diye arattığında AWS'nin resmî
`PutObject` sayfasını bulursun. `resource` ile arada bir çeviri katmanı olur, hata
mesajını dokümanla eşleştiremezsin.

**Junior tuzağı:** Stack Overflow cevaplarının çoğu 2016–2019 arası ve `resource` kullanıyor.
Kopyalayınca çalışır, ama yeni bir ihtiyaç çıktığında `resource`'ta o metot olmadığını
görüp yarı yolda `client`'a geçmek zorunda kalırsın. Baştan `client` seç.

---

## 5. `Session` — ne zaman gerekir

`boto3.client("s3")` aslında bir kısayol: arka planda **default session** oluşturur.
Session = kimlik + bölge + yapılandırmanın paketi.

```python
session = boto3.Session(profile_name="prod", region_name="eu-central-1")
s3 = session.client("s3")
```

Ne zaman lazım: aynı programda **iki farklı hesaba** ya da iki farklı bölgeye bağlanmak
gerektiğinde. Bizim projede gerekmeyecek — tek hesap, tek bölge. Ama gördüğünde tanı.

---

## 6. Yanlış anlaşılan noktalar

| Barış önce şöyle sandı | Aslında |
|---|---|
| "AWS bir web sitesi, kod ayrı bir dünya" | AWS bir API. Konsol o API'nin sadece bir istemcisi. Konsolda yaptığın her şey koddan da yapılabilir |
| "`boto3` sadece bağlantı kütüphanesi" | İmzalama, retry, sayfalama, hata dönüşümü de onun işi. Kendi yazsan yüzlerce satır |
| "Secret access key AWS'ye gönderiliyor" | Gönderilmiyor. İmza anahtarı olarak kullanılıyor, ağda sadece **imza** gidiyor |
| "`pip install boto3` yeter, çalışır" | Kütüphane kurulur ama kimlik bilgisi yoksa `NoCredentialsError` alırsın. İkisi ayrı iş |
| "AWS CLI kurulunca `boto3` da kurulmuş olur" | Hayır. CLI bir Windows uygulaması, `boto3` bir Python paketi. İkisi ayrı ayrı kurulur. **Ortak olan tek şey `~/.aws/` dosyalarıdır** |

---

## 7. Kanıt

`boto3` henüz kurulu değil (P2.2'de `pyproject.toml`'a girecek). Ama CLI'ın da aynı API'yi
çağırdığı **şimdi** ölçülebilir:

```bash
aws s3api list-buckets --debug 2>&1 | grep -i "Making request\|AWS4-HMAC-SHA256" | head -5
```

Beklenen: `Making request for OperationModel(name=ListBuckets)` benzeri bir satır ve
`Authorization` başlığında `AWS4-HMAC-SHA256` ifadesi.

Bu iki şeyi kanıtlar:

1. `aws s3api list-buckets` bir **HTTP isteğidir**, sihir değil — `boto3` de aynısını yapacak
2. İmza yöntemi **SigV4**'tür ve giden şey secret değil, **imzadır**

> `--debug` çıktısı çok uzundur ve içinde access key **ID**'si görünür (bu gizli değil).
> Secret **görünmez** — göreceğin en yakın şey imza dizisidir. Yine de ekran paylaşırken
> `--debug` çalıştırma alışkanlığı edinme.

---

## 8. Bir sonraki turda (bu projede yok)

- `Config(retries={"mode": "adaptive"})` — retry davranışını elle ayarlamak
- Paginator'lar: `client.get_paginator("list_objects_v2")` — 1000'den fazla nesne listelemek
- `moto` kütüphanesi — testlerde AWS'yi taklit etmek (gerçek çağrı yapmadan)
- `aiobotocore` — asenkron `boto3`

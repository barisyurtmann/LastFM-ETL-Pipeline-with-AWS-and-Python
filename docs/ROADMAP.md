# Yol Haritası

Bu dosya **planı** tutar: hangi adım, hangi alt adımlar, ne zaman bitmiş sayılır.

> **Burada durum bilgisi yoktur.** Nerede kaldığımız için → [`PROGRESS.md`](PROGRESS.md)
> Sabit sözleşme (hedef, tercihler, mimari) için → [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md)

---

## Bu planın kaynağı

Plan, DataVidhya "Spotify Pipeline" dersinin **dört parçasından** türetildi. Kapsam
o dört parçadır — ne eksik, ne fazla.

| Ders | Konu | Bu roadmap'te |
|---|---|---|
| P1 | Mimari, API kimlik bilgileri, AWS servisleri, S3 bucket'ları | **Adım P1** |
| P2 | Local Python: extract + nested JSON'u tablolara düzleştir | **Adım P2** |
| P3 | İki Lambda, layer, env var, CloudWatch + S3 tetikleyicileri, IAM | **Adım P3** |
| P4 | Glue Crawler, Data Catalog, Athena SQL | **Adım P4** |

**Kurstan tek farkı:** kurs kodu konsola yapıştırıyor, biz repoya yazıyoruz. Öğrenilecek
şey mimari değil, mimarinin etrafındaki mühendislik.

---

## Öğrenilecek "structure" — bu tablo planın özüdür

Her satır bir alt adımın varlık sebebi. Kurs sol sütunu yapıyor; biz sağ sütunu.

| # | Kurs ne yapıyor | Profesyonel karşılığı | Nerede |
|---|---|---|---|
| 1 | `client_id = "your_client_id"` kodda | `.env` + fail-fast doğrulama, sır repoda değil | P1.1 |
| 2 | Root hesapla konsola giriliyor | IAM kullanıcı, least privilege, budget alarm | P1.2 |
| 3 | Bucket adı `spotify-etl-raw-darshil` | İsimlendirme kuralı, public access blok, versioning | P1.3 |
| 4 | Tek dosyada 200 satır | `src/lastfm_etl/` modülleri, sorumluluk sınırı | P2.1, P2.3 |
| 5 | Hata yolu yok, sadece mutlu yol | timeout, `error` koduna göre retry, gürültülü patlama | P2.1 |
| 6 | Test yok | `pytest` + elde duran fixture'lar (ADR-0004) | P2.4 |
| 7 | Kod konsol editörüne yapıştırılıyor | zip paketleme — versiyonlanabilir, `git`'te duran deploy | P3.1 |
| 8 | `AmazonS3FullAccess` | Least-privilege policy, tek rol, tek bucket | P3.4 |
| 9 | README yok | Mimari şeması + çalıştırma + maliyet tablosu | P4.3 |

---

## Kurallar

- **Tek seferde tek alt adım.** P2.1 bitmeden P2.2'ye geçilmez.
- **Not koddan sonra yazılır ve hiçbir adımı bloklamaz.** Uzunluk sınırı yok, sıra sınırı var.
- **ADR sadece geri alması pahalı kararlar için.**
- **14 alt adım bir bütçedir.** Yeni alt adım ancak bir eskisi silinerek eklenir.
- Bir alt adım "kursta yok" ve "structure de değil" ise → `Sonraki tur` bölümüne.

---

## Akış

```
Last.fm API
    │
    ▼
EventBridge (günlük)  ──►  Lambda: extract  ──►  S3 raw bucket
                                                  raw/to_processed/*.json
                                                       │
                                                  (PUT event)
                                                       ▼
                                              Lambda: transform
                                                       │
                                    ┌──────────────────┴─────────────┐
                                    ▼                                ▼
                        S3 transformed bucket              raw/processed/ (arşiv)
                        tracks/  artists/  (parquet)
                                    │
                                    ▼
                            Glue Crawler
                                    │
                                    ▼
                          Glue Data Catalog
                                    │
                                    ▼
                              Athena (SQL)
```

**Bağımlılık düz bir çizgi:** P1 → P2 → P3 → P4. Paralel iş yok.

---

## Adım P1 — Kurulum ve hesaplar

> Ders P1'in karşılığı. Kod yazılmıyor; hesap, sır ve depolama hazırlanıyor.

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P1.1 | `.env`'den config okuma, eksik/boş key'de **fail-fast**, sırrın loga ve `repr()`'e sızmaması | Kimlik bilgileri kodda yazılı | Sır nerede durur, kim okur, nasıl doğrulanır |
| P1.2 | AWS hesabı: **IAM kullanıcı** (root değil), `aws configure`, **budget alarm** | Anlatılmıyor | Least privilege; korkuluk harcamadan **önce** kurulur |
| P1.3 | İki S3 bucket (`raw`, `transformed`): isimlendirme, public access blok, versioning, klasör şeması | Konsoldan iki bucket | Geri dönülemez silme, isim çakışması, erişim varsayılanı |

**Bitti tanımı:**

- [ ] `python -c "from lastfm_etl.config import load; print(load())"` çalışıyor ve sırrı **basmıyor**
- [ ] `.env` boşken aynı komut **gürültülü** patlıyor, `echo $?` sıfır değil
- [ ] `aws s3 ls` root ile değil, IAM kullanıcısıyla çalışıyor
- [ ] Budget alarm kurulu (eşik: aylık $5)
- [ ] İki bucket var, ikisi de public erişime kapalı
- [ ] `.env` `git status`'ta görünmüyor

**Not adayı:** AWS kimlik zinciri — `~/.aws/credentials` neden proje `.env`'inde değil

---

## Adım P2 — Local: extract → transform → Parquet

> Ders P2'nin karşılığı. Bütün iş mantığı burada yazılıyor ve **çalıştığı görülüyor.**
> P3 bu kodu taşır, yeniden yazmaz. **S3 bu adımda yok** (ADR-0016) — çıktı local
> `data/` altına yazılır, ilk S3 yazımı P3'tedir.

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P2.1 | Extract modülü: `requests`, `format=json`, `timeout`, **gövdeyi status'tan önce oku**, `error` koduna göre retry, top-100 sayfalama (ADR-0006, ADR-0015) | `spotipy` her şeyi gizliyor; hata yolu yok | Modül sınırı; hata yönetimi baştan, süs olarak değil |
| P2.2 | Transform modülü: nested JSON → `tracks` + `artists`, **`rank`'i `@attr` + sayfa içi konumdan üret**, `drop_duplicates`, açık tip dönüşümü | 3 tablo, düzleştirme `spotipy` çıktısından | Düzleştirme, foreign key, açık tip; türetilmiş alanın nerede üretildiği |
| P2.3 | Load modülü: satırlar → **JSON Lines byte'ları** (satır başına bir nesne) → local `data/` altına yaz. Aynı fonksiyon P3'te S3'e yazacak — hedef değişir, üretim değişmez | CSV, doğrudan S3'e | Byte üretimi ile hedefe yazmanın ayrılması; serileştirme formatının sorgu motoruyla sözleşmesi |
| P2.4 | Local uçtan uca çalıştır + `pytest` (fixture'larla, **ağsız**) | Test yok | Testin ne olduğu; fixture'ın neden kaydedildiği |

**Bitti tanımı:**

- [ ] `data/tracks/` ve `data/artists/` altında gerçek JSON Lines dosyaları var
- [ ] Dosyalar **satır başına tek JSON nesnesi** — Athena'nın JsonSerDe'sinin tek kabul ettiği biçim
- [ ] `tracks` tablosunda `(snapshot_date, rank)` tekrar etmiyor
- [ ] `rank` 1'den başlıyor ve sayfa sınırında **kırılmıyor** (51. kayıt `rank=51`)
- [ ] Hiçbir sayısal alan string kalmadı (`playcount`, `duration`, `listeners`)
- [ ] Bozuk `api_key` ile **gürültülü** patlıyor
- [ ] Bozuk/eksik alanlı bir kayıt geldiğinde davranış **yazılı**: at, null'la, yoksa patlat
- [ ] `pytest` ağ ve gerçek sır olmadan geçiyor
- [ ] **Aynı gün iki kez çalıştırıldığında ne olduğu yazılı ve kasıtlı** (ADR-0016: aynı
      key'in üzerine yazılır)

**ADR adayı:** Write the curated layer as JSON Lines instead of Parquet · Define the
curated schema and its explicit types

**Not adayı:** Nested JSON düzleştirme kalıpları · Serileştirme formatları (JSON Lines vs
CSV vs Parquet) ve sorgu motoruyla sözleşmesi · pytest ve fixture · ETL vs ELT ve raw
katmanın bedeli

---

## Adım P3 — AWS'ye taşı

> Ders P3'ün karşılığı: *"deploy this code to AWS Lambda, set up the CloudWatch trigger
> for daily execution, and store the data in S3."*
> **İş mantığı yazılmaz** — P2'nin fonksiyonları paketlenir ve tetikleyiciye bağlanır.
> İş mantığı değişiyorsa P2 yanlış yazılmıştır.

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P3.1 | Lambda handler: `handler(event, context)` → P2'nin üç fonksiyonunu sırayla çağırır. **Tek Lambda** (ADR-0016) | Kod konsol editöründe | Handler bir **adaptördür**, iş mantığı taşımaz |
| P3.2 | Paketleme: zip artefaktı + bağımlılık layer'ı (yalnızca `requests`; `boto3` runtime'da hazır), env var, `timeout`, `memory` | Konsola yapıştırma | Deploy edilebilir artefakt; layer neden var, ne zaman gerekmiyor |
| P3.3 | S3'e yaz: P2.3'ün load fonksiyonu, hedef `lastfm-etl-transformed-<ek>`. Key: `tracks/snapshot_date=<YYYY-MM-DD>/tracks.json` | Aynı | Partition'lı key şeması; Athena'nın neden umursadığı |
| P3.4 | Tetikleyici + IAM: EventBridge günlük cron, Lambda için **tek least-privilege rol** | `AmazonS3FullAccess` | Zaman-tabanlı tetik; kullanıcı → rol geçişi |

**Bitti tanımı:**

- [ ] Lambda, P2'nin **aynı fonksiyonlarını** çağırıyor — ikinci bir kopya yok
- [ ] Elle tetiklendi, `transformed` bucket'ta Parquet oluştu
- [ ] EventBridge kuralı kurulu ve bir sonraki koşu zamanı görünüyor
- [ ] Rol politikasında `*` yok; yalnızca tek bucket'a `PutObject`
- [ ] Lambda patladığında CloudWatch Logs'ta teşhise yeten satır var
- [ ] Lambda `statusCode` hatada başarılı görünmüyor
- [ ] **Aynı günü iki kez çalıştırınca ikinci koşu birincinin üzerine yazıyor**, yeni
      dosya birikmiyor

**ADR adayı:** Package the Lambda as a zip rather than a container image

**Not adayı:** Lambda çalışma modeli (cold start, layer, timeout, `/tmp`) · EventBridge
cron ifadeleri · Lambda handler imzası ve `event`/`context`

---

## Adım P4 — Catalog + sorgu

> Ders P4'ün karşılığı. Pipeline burada **kanıtlanır.**

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P4.1 | Glue Crawler: tek veri bucket'ını tara, `lastfm_db` oluştur, iki tablo, **JSON'dan çıkarılan tipleri doğrula** (tarih alanları string gelir) | Aynı | Şema çıkarımı; JSON'da tip neyi taşır neyi taşımaz |
| P4.2 | Athena: sonuç konumu ayarı, ilk `SELECT`, `tracks ⋈ artists` JOIN | Aynı | Metastore + sorgu motoru ayrımı; `$5/TB` maliyet modeli |
| P4.3 | README: mimari şeması, çalıştırma adımları, **maliyet tablosu** | README yok | Portfolyo vitrini; bir yabancının projeyi çalıştırabilmesi |

**Bitti tanımı:**

- [ ] Glue'da iki tablo var, kolon tipleri doğru (`col0`, `col1` yok)
- [ ] Athena'da JOIN'li bir sorgu doğru sonuç döndürüyor
- [ ] Bir sorgunun **taranan byte'ı** okundu, maliyeti hesaplandı
- [ ] Crawler'ın koşu maliyeti biliniyor (~$0.44/koşu)
- [ ] README'deki komutlar kopyala-yapıştır ile çalışıyor
- [ ] **Pipeline elle müdahale olmadan bir gün çalıştı ve veri geldi**

**Not adayı:** Data Catalog / metastore nedir · Athena maliyet modeli ve partition

---

## Sonraki tur (bu projede değil)

Bunlar kursta **yok** ve structure dersi de **değil**. İş sırasında akla gelirse
buraya yazılır, plana değil:

`ruff` + GitHub Actions CI · Terraform (IaC) · dbt · partition (`dt=`) ve partition
pruning · CloudWatch alarm · Snowflake · Airflow/Dagster · streaming · mypy · Docker ·
`chart.getTopArtists` gibi ikinci bir endpoint

**Kurstan bilinçli olarak alınmayanlar:**

- **Spotify API** → Last.fm. Sebep: Adım 1'de Last.fm ölçüldü, key alındı, fixture
  kaydedildi (ADR-0004/0005/0006). Değiştirmek o işi çöpe atar. Last.fm ayrıca daha
  basit: OAuth yok, tek `api_key` parametresi.
- **`spotipy`** → düz `requests`. Last.fm'in resmî wrapper'ı yok, ve zaten hata yolunu
  gizleyen kütüphane bu projede öğrenilecek şeyi de gizler.
- **3 tablo** → **2 tablo** (`tracks`, `artists`). `chart.getTopTracks` album
  döndürmüyor. JOIN dersi korunuyor.
- **CSV** → **Parquet**. Crawler CSV'de tipi tahmin eder (kurs bile header uyarısı
  yazmış); Parquet tipi kendi taşır. Değişiklik `to_csv` → `to_parquet`.

---

## Kursun kodundaki, farkında olunması gereken üç şey

Bunlar kursu kötülemek için değil — plan bunları **bilerek** ele alıyor.

1. **Transform Lambda yarış durumuna açık.** Kurs kodu S3 PUT ile tetiklenip
   `to_processed/` altındaki **bütün** dosyaları listeleyip döngüye giriyor. İki dosya
   arka arkaya düşerse iki invocation aynı dosyayı işler. → P3.2'de ele alınacak.
2. **`AmazonS3FullAccess`.** Kurs bunu kendisi "production'da yapma" diye işaretlemiş.
   → P3.4.
3. **Zaman damgalı dosya adı = idempotency yok.** Aynı gün iki koşu iki dosya üretir ve
   Athena ikisini de sayar. → P2.2 ve P3.2'de karar verilecek.

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
| 8 | `AmazonS3FullAccess` | Least-privilege policy, iki role ayrı | P3.4 |
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

## Adım P2 — Local: extract + transform

> Ders P2'nin karşılığı. Bütün iş mantığı burada yazılıyor ve **çalıştığı görülüyor.**
> P3 bu kodu taşır, yeniden yazmaz.

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P2.1 | Extract modülü: `requests`, `format=json`, `timeout`, **gövdeyi status'tan önce oku**, `error` koduna göre retry, top-100 sayfalama (ADR-0006) | `spotipy` her şeyi gizliyor; hata yolu yok | Modül sınırı; hata yönetimi baştan, süs olarak değil |
| P2.2 | Raw'ı S3'e yaz: `boto3.put_object`, key şeması `raw/to_processed/lastfm_raw_<ts>.json` | Aynı | Raw immutability; ham veri **hiç dokunulmadan** saklanır |
| P2.3 | Transform modülü: nested JSON → `tracks` + `artists`, `drop_duplicates`, tip dönüşümü, **Parquet** | 3 tablo, CSV | Düzleştirme, foreign key, açık tip |
| P2.4 | Local uçtan uca çalıştır + `pytest` (fixture'larla, ağsız) | Test yok | Testin ne olduğu; fixture'ın neden kaydedildiği |

**Bitti tanımı:**

- [ ] `raw` bucket'ta gerçek JSON var — S3'te, local `data/` klasöründe değil
- [ ] `transformed` bucket'ta `tracks/` ve `artists/` altında Parquet var
- [ ] Bozuk `api_key` ile **gürültülü** patlıyor
- [ ] `tracks` tablosunda `(snapshot_date, rank)` tekrar etmiyor
- [ ] Hiçbir sayısal alan string kalmadı (`playcount`, `duration`, `listeners`)
- [ ] Bozuk/eksik alanlı bir kayıt geldiğinde davranış **yazılı**: at, null'la, yoksa patlat
- [ ] `pytest` ağ ve gerçek sır olmadan geçiyor
- [ ] **Aynı gün iki kez çalıştırıldığında ne olduğu yazılı ve kasıtlı**

**ADR adayı:** Define the curated schema and its explicit types

**Not adayı:** Nested JSON düzleştirme kalıpları · Parquet vs CSV · pytest ve fixture

---

## Adım P3 — AWS'ye taşı

> Ders P3'ün karşılığı. **İş mantığı yazılmaz** — P2'nin fonksiyonları paketlenir ve
> tetikleyicilere bağlanır. İş mantığı değişiyorsa P2 yanlış yazılmıştır.

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P3.1 | Extract Lambda: **zip paketleme**, bağımlılık layer'ı, env var, `timeout` 1 dk, `memory` 256 MB | Kod konsol editöründe | Deploy edilebilir artefakt; `git`'te duran kod |
| P3.2 | Transform Lambda: `get_object` → dönüştür → `put_object` → dosyayı `to_processed/` → `processed/` taşı | Aynı | Yeniden işlemeyi önleyen dosya taşıma = **idempotency mekanizması** |
| P3.3 | Tetikleyiciler: EventBridge günlük cron + S3 `PUT` (prefix `raw/to_processed/`, suffix `.json`) | Aynı | Zaman-tabanlı vs olay-tabanlı tetik; filtre neden zorunlu |
| P3.4 | IAM: iki Lambda için **ayrı least-privilege rol** | `AmazonS3FullAccess` | Kullanıcı → rol geçişi; rolün neden kullanıcıdan farklı olduğu |

**Bitti tanımı:**

- [ ] Lambda, P2'nin **aynı fonksiyonunu** çağırıyor — ikinci bir kopya yok
- [ ] Extract Lambda elle tetiklendi, `raw` bucket'ta dosya oluştu
- [ ] O dosya transform Lambda'yı **kendiliğinden** tetikledi
- [ ] Dosya `processed/` altına taşındı, `to_processed/` boş
- [ ] Rol politikalarında `*` yok, iki rol ayrı
- [ ] Lambda patladığında CloudWatch Logs'ta teşhise yeten satır var
- [ ] `echo $?` / Lambda `statusCode` hatada başarılı görünmüyor

**ADR adayı:** Package Lambdas as zip rather than container images

**Not adayı:** Lambda çalışma modeli (cold start, layer, timeout) · S3 event semantiği

---

## Adım P4 — Catalog + sorgu

> Ders P4'ün karşılığı. Pipeline burada **kanıtlanır.**

| # | Alt adım | Kursta | Structure dersi |
|---|---|---|---|
| P4.1 | Glue Crawler: `transformed` bucket'ı tara, `lastfm_db` oluştur, iki tablo, tipleri **doğrula** | Aynı | Şema çıkarımı; Crawler'ın ne zaman gereksiz olduğu |
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

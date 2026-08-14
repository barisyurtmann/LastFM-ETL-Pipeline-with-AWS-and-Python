# Veri araçları manzarası

> **Bu dosya bir adım notu değil, bir başvuru haritasıdır.** `docs/notes/` altındaki notlar
> bir alt adıma bağlıdır ve o anın öğrenmesini dondurur. Bu dosya araç seçerken açılır ve
> öğrendikçe **güncellenir**.
>
> | Belge | Ne | Değişir mi |
> |---|---|---|
> | `docs/adr/` | Bu projeye özel karar | **Asla** — yeni ADR supersede eder |
> | `docs/notes/` | Bir alt adımda öğrenilen genel bilgi | Nadiren |
> | **`docs/TOOLING.md`** | **Araç manzarası ve seçim kriterleri** | **Sık — canlı belge** |

## İçindekiler

| § | Bölüm |
|---|---|
| [1](#1-iki-eksen-aşama--katman) | İki eksen: aşama × katman |
| [2](#2-etl-mi-elt-mi--manzarayı-bu-ayrım-belirledi) | ETL mi ELT mi |
| [3](#3-extract--veriyi-kaynaktan-çıkarmak) | **Extract** |
| [4](#4-load--hedefe-yazmak) | **Load** |
| [5](#5-transform--veriyi-işe-yarar-hâle-getirmek) | **Transform** |
| [6](#6-depolama-dosya-formatı-tablo-formatı-göl-ambar) | Depolama: dosya formatı, tablo formatı, göl/ambar |
| [7](#7-işleme-motorları) | İşleme motorları |
| [8](#8-orkestrasyon) | Orkestrasyon |
| [9](#9-veri-kalitesi-ve-gözlemlenebilirlik) | Veri kalitesi ve gözlemlenebilirlik |
| [10](#10-katalog-ve-yönetişim) | Katalog ve yönetişim |
| [11](#11-streaming--batch-dışı-dünya) | Streaming |
| [12](#12-serve-bi-ve-reverse-etl) | Serve: BI ve reverse ETL |
| [13](#13-altyapı-ve-dağıtım) | Altyapı ve dağıtım |
| [14](#14-bulut-karşılıkları-matrisi) | **Bulut karşılıkları matrisi** |
| [15](#15-boyut-sezgisi--en-işe-yarar-tek-kural) | Boyut sezgisi |
| [16](#16-maliyet-modelleri--bu-tasarımı-değiştirir) | **Maliyet modelleri** |
| [17](#17-karar-sırası--hangi-soru-önce) | Karar sırası |
| [18](#18-bu-projede-roadmap-adımı--araç-kategorisi) | **Bu projede: ROADMAP adımı → araç** |
| [19](#19-junior-tuzakları) | Junior tuzakları |
| [20](#20-mülakat) | Mülakat |
| [21](#21-sözlük) | Sözlük |

---

## 1. İki eksen: aşama × katman

Araçlar iki farklı şekilde gruplanır ve ikisini birden bilmek gerekir.

**Eksen 1 — boru hattı aşaması:** Extract → Load → Transform → Serve.
Verinin başına gelen şeyler.

**Eksen 2 — altyapı katmanı:** depolama, motor, katalog, orkestrasyon, kalite.
Aşamaların üstünde durduğu zemin.

Kafa karışıklığının kaynağı, iki eksendeki araçları birbirinin rakibi sanmaktır.
*"PySpark mı Snowflake mı"* sorusu, *"çekiç mi ev mi"* gibidir.

### Ana matris

| Aşama / katman | Ne yapar | Açık kaynak / self-hosted | Yönetilen (ücretli) |
|---|---|---|---|
| **Extract + Load (EL)** | Kaynaktan al, hedefe yaz | dlt, Airbyte, Meltano/Singer, Debezium, Kafka Connect, NiFi | Fivetran, Estuary, AWS DMS, AppFlow, Confluent Cloud |
| **Transform (T)** | Ham veriyi modele çevir | dbt Core, SQLMesh, Spark, Flink, polars, DuckDB | dbt Cloud, Databricks, Snowflake, BigQuery |
| **Depolama + tablo formatı** | Veri nerede, nasıl durur | Parquet + Iceberg / Delta Lake / Hudi, MinIO | S3, GCS, ADLS, Snowflake, Databricks, S3 Tables |
| **Sorgu / serve** | Okuma, analiz | Trino, DuckDB, ClickHouse, Druid, Pinot, StarRocks | Athena, BigQuery, Snowflake, ClickHouse Cloud |
| **Orkestrasyon** | Ne zaman, hangi sırayla | Airflow, Dagster, Prefect, Kestra, Mage, Argo | Astronomer, Dagster+, MWAA, Cloud Composer, Step Functions |
| **Kalite + gözlemlenebilirlik** | Veri doğru mu, boru hattı sağlıklı mı | Great Expectations, Soda Core, dbt tests, Elementary, OpenLineage | Monte Carlo, Bigeye, Metaplane |
| **Katalog + yönetişim** | Ne var, kime ait, kim erişebilir | Hive Metastore, DataHub, OpenMetadata, Apache Polaris, Unity Catalog OSS | Glue Data Catalog, Unity Catalog, Purview, Atlan, Collibra |
| **Altyapı** | Bunlar nerede çalışıyor | Terraform, Docker, Kubernetes | Managed K8s, bulut servisleri |

> **En önemli ilke:** modern bir veri platformu bir ürün listesi değil, **işlevsel katmanlar
> kümesidir**. Bir araç birden çok katmanı kapsayabilir — ClickHouse hem depolar hem sorgular,
> Databricks neredeyse hepsini yapar. Katmanı bil, ürünü sonra seç.

---

## 2. ETL mi ELT mi — manzarayı bu ayrım belirledi

Araç listesinin neden böyle göründüğünü anlamanın anahtarı bu.

| | **ETL** (klasik) | **ELT** (modern varsayılan) |
|---|---|---|
| Sıra | Extract → **Transform** → Load | Extract → **Load** → Transform |
| Dönüşüm nerede | Ayrı bir işleme sunucusunda, hedefe yazmadan **önce** | Hedefin (ambar/göl) **içinde**, SQL ile |
| Hedefe giren | Temizlenmiş veri | **Ham veri** |
| Tipik araçlar | Informatica, Talend, SSIS, elle Spark | Fivetran/Airbyte/dlt + **dbt** |
| Neden ortaya çıktı | Depolama ve hesap pahalıydı; ambara çöp koymak lüks | Bulut ambarlarında depolama ucuzladı, hesap elastikleşti |

**ELT'nin kazandırdığı — ve bu projeyle doğrudan ilgili olan:**

Ham veri hedefte durduğu için, dönüşümü yanlış yaptığında **yeniden işleyebilirsin**.
ETL'de dönüşüm yazmadan önce olur; yanlışsa veri geri gelmez, kaynağı yeniden çekmen
gerekir — çekilemiyorsa kayıptır.

> Bu, bizim `raw/` + `curated/` ayrımımızın tam olarak sebebidir. Adım 4 ve 5'i ayırmamız
> ELT desenidir. Not 15 §0'daki *"raw katman yoksa hiçbir alanı elemeye hakkın yok"*
> cümlesi de buradan gelir.

**EtLT** diye bir ara desen de vardır: yüklemeden önce yalnızca **teknik** dönüşümler
(tip düzeltme, PII maskeleme, format çevirme), **iş** dönüşümleri ise hedefte. PII'yi
ambara hiç sokmamak gereken durumlarda zorunludur.

---

## 3. Extract — veriyi kaynaktan çıkarmak

Doğru aracı **kaynağın tipi** belirler.

### 3.1 REST / SaaS API'leri

| Araç | Model | Ne zaman |
|---|---|---|
| **Elle Python** (`httpx`, `requests`) | Tam kontrol | Kaynak tuhaf, hazır konnektör yok, veya öğreniyorsun |
| **dlt** | Python kütüphanesi, OSS | REST API'ler. Sayfalama, auth, incremental, şema çıkarımı hazır gelir |
| **Airbyte** | Konnektör platformu, OSS + Cloud | Çok sayıda standart kaynak, self-host edilebilir |
| **Meltano / Singer** | Konnektör spesifikasyonu + çerçeve | Singer "tap/target" ekosistemi; olgun ama dağınık |
| **Fivetran** | Tamamen yönetilen, ücretli | Bütçe var, mühendislik zamanı yok |

### 3.2 Veritabanları — CDC (Change Data Capture)

Bir üretim veritabanından veri çekmenin iki yolu vardır ve fark kritiktir:

| Yöntem | Nasıl | Sorunu |
|---|---|---|
| **Sorgu tabanlı** | `WHERE updated_at > son_çalışma` | Silinen satırları **göremezsin**. `updated_at` güncellenmemişse kaçırırsın. Kaynağa yük biner |
| **Log tabanlı (CDC)** | Veritabanının **replikasyon log'unu** okur (MySQL binlog, Postgres WAL) | Kurulum karmaşık, izin gerekir. Ama silmeleri de yakalar, kaynağa yük bindirmez |

| Araç | Not |
|---|---|
| **Debezium** | CDC'nin fiili açık kaynak standardı. Kafka Connect üzerinde veya bağımsız sunucu olarak |
| **AWS DMS** | Yönetilen replikasyon; bulut içi göçler ve CDC |
| **Estuary Flow** | Yönetilen, streaming odaklı CDC + ETL |
| Fivetran / Airbyte | İkisi de CDC konnektörleri sunar |

> **Mülakat sorusu:** *"Silinen satırları nasıl yakalarsın?"* Sorgu tabanlı çekimde
> yakalayamazsın — bu, CDC'nin var olma sebebidir.

### 3.3 Dosyalar ve nesne depolama

`boto3` / `s3fs` / `adlfs`, `rclone`, SFTP istemcileri. Genelde ayrı bir araca gerek
yoktur; ingestion çerçevesinin dosya kaynağı yeterlidir.

### 3.4 Akış kaynakları

Kafka Connect, Kinesis, Pub/Sub, Event Hubs. → §11.

### 3.5 Web scraping

Scrapy, Playwright, BeautifulSoup. Son çare: API varsa API kullanılır. Scraping kırılgandır
ve hukuki tarafı vardır.

### Extract'te karar ekseni

**Kaynak standart mı?** Standartsa hazır konnektör; değilse `dlt` veya elle.

Kritik nokta — hazır konnektör **kararı senin yerine vermez**. Airbyte ve dlt sana şunları
sorar ve cevabı senden ister: primary key, incremental cursor alanı, write disposition,
veri response'un neresinde. Bunlar bu projede ADR-0005, ADR-0006 ve 1.7'de verdiğin
kararların aynısıdır.

---

## 4. Load — hedefe yazmak

Modern araçlarda Extract ve Load genelde birlikte gelir ("EL"), ama yükleme kendi
kararlarını taşır.

### 4.1 Yükleme stratejileri — en önemli tablo

| Strateji | Ne yapar | Ne zaman | Riski |
|---|---|---|---|
| **Full refresh** | Hedefi silip baştan yaz | Küçük tablo, karmaşıklık istemiyorsun | Kaynak bozuksa hedefi de bozarsın |
| **Append** | Sadece ekle | Olay kaydı, snapshot | Tekrar çalışırsa **çiftler** — idempotency gerekir |
| **Upsert / merge** | Anahtara göre varsa güncelle yoksa ekle | Değişen kayıtlar | Anahtar yanlışsa sessizce yanlış veri |
| **Partition overwrite** | Yalnızca ilgili bölümü değiştir | Tarihe göre bölünmüş veri | — |
| **SCD Type 2** | Değişimi yeni satır olarak tut, geçmişi koru | Boyut tablosunda geçmiş gerekiyorsa | Tablo büyür, sorgu karmaşıklaşır |

> Bu projede **partition overwrite** seçildi ve bu bedava gelmedi: anahtara `snapshot_date`
> girdiği için aynı günün tekrar koşusu aynı anahtarı üretiyor, dolayısıyla bölümün üzerine
> yazmak idempotent oluyor. ADR-0005'in sonucu.

### 4.2 Hedefe göre yükleme aracı

| Hedef | Toplu yükleme yolu |
|---|---|
| **S3 / GCS / ADLS** | `pyarrow`, `polars`, Spark writer, `deltalake`, `pyiceberg` |
| **Snowflake** | `COPY INTO` (toplu), Snowpipe (sürekli) |
| **BigQuery** | Load jobs, Storage Write API |
| **Redshift** | `COPY` (S3'ten) |
| **Postgres** | `COPY` — `INSERT` döngüsünden onlarca kat hızlıdır |
| **ClickHouse** | Native protokol, toplu insert |

> **Junior tuzağı:** satır satır `INSERT`. Her veritabanının toplu yükleme yolu vardır ve
> aradaki fark 10–100 kat olabilir. `for row in rows: cursor.execute(INSERT...)` gördüğün
> her yerde bir toplu alternatif vardır.

---

## 5. Transform — veriyi işe yarar hâle getirmek

Üç ayrı yol vardır ve seçim "hangisi daha iyi" değil, "işin doğası ne" sorusudur.

### 5.1 SQL yolu — dbt ve benzerleri

| Araç | Not |
|---|---|
| **dbt Core** | Fiili standart. SQL modelleri, bağımlılık grafiği, testler, dokümantasyon, lineage, incremental model |
| **SQLMesh** | dbt alternatifi. Sütun seviyesinde lineage, sanal veri ortamları, plan/apply akışı |
| **Dataform** | Google tarafında, BigQuery'ye entegre |

**dbt bir işleme motoru değildir.** Veriye dokunmaz: senin SQL'ini alır, bağımlılık
sırasına dizer, `CREATE TABLE AS` üretir ve **başka bir motora gönderir**. dbt + Snowflake,
dbt + BigQuery, dbt + DuckDB, dbt + Athena. Motor olmadan dbt hiçbir şey hesaplamaz.
**En sık karıştırılan şey budur.**

dbt'nin gerçek kazancı SQL yazmak değil; **bağımlılık grafiği, testler, lineage ve
incremental model semantiği**. Bunlara ihtiyacın yoksa dbt saf ek yüktür.

| dbt kullan | Kullanma |
|---|---|
| Dönüşümler SQL ve bir motor üzerinde | Dönüşüm tek bir Python script'i |
| Birbirine bağımlı çok sayıda model | 1–2 tablo |
| Test, doküman, lineage bedava gelsin | İş Python gerektiriyor (ML, karmaşık parse, API çağrısı) |

### 5.2 Python / DataFrame yolu

| Araç | Ölçek | Not |
|---|---|---|
| **pandas** | Tek makine, bellekte | Keşif ve prototip. Üretimde büyük veride sorunlu |
| **polars** | Tek makine, çok çekirdek, lazy | pandas'ın modern alternatifi; Rust, çok hızlı |
| **DuckDB** | Tek makine, sütunlu, SQL | Parquet'i doğrudan sorgular, sunucu yok |
| **PySpark** | Dağıtık | TB ölçeği |
| **Dask** | Dağıtık Python | pandas API'sini ölçekler; Spark'a göre niş |
| **Ibis** | Arka uç bağımsız DataFrame API | Aynı kodu DuckDB/BigQuery/Spark üzerinde çalıştırır |

### 5.3 Streaming yolu

Flink, Spark Structured Streaming, Kafka Streams, Materialize, RisingWave → §11.

### Hangi yol

| Durum | Yol |
|---|---|
| Veri zaten ambarda, dönüşüm ilişkisel | **SQL / dbt** |
| Dönüşüm SQL'de ifade edilemiyor (parse, ML, API çağrısı) | **Python** |
| Veri dosya sisteminde, ambar yok | **Python (polars/DuckDB)** veya Trino/Athena |
| Gecikme saniyeler mertebesinde olmalı | **Streaming** |

---

## 6. Depolama: dosya formatı, tablo formatı, göl / ambar

Üç ayrı kavram, sürekli karıştırılır.

### 6.1 Dosya formatı

| Format | Yapı | Ne zaman |
|---|---|---|
| CSV | Satır, tipsiz | İnsan okuyacaksa veya sistemler arası takas. **Analitik depolama için asla** |
| JSON / JSONL | Satır, iç içe | Ham katman, şemasız veya iç içe veri |
| Avro | Satır, şemalı | Streaming, Kafka, şema evrimi |
| **Parquet** | **Sütunlu** | **Analitik depolamanın varsayılanı** |
| ORC | Sütunlu | Hive ekosistemi mirası |

**Sütunlu neden kazanıyor:** analitik sorgular *çok satırın az kolonunu* okur. Sütunlu
formatta yalnızca gereken kolonlar diskten okunur; ayrıca aynı tipteki değerler yan yana
durduğu için sıkıştırma çok daha iyidir. Satır formatları kaydın **tamamını** yazıp
okuduğun yerlerde kazanır — streaming, olay kaydı, OLTP.

### 6.2 Tablo formatı — dosya formatından farklı bir katman

Bir klasör dolusu Parquet dosyasının **olmayan** şeyleri: atomik commit, eşzamanlı yazarlar
arasında izolasyon, güvenli şema değişimi, satır güncelleme/silme, geçmişe bakma.

**Apache Iceberg / Delta Lake / Apache Hudi** bu dosyaların üstüne bir **metadata katmanı**
koyar ve bunları kazandırır. Iceberg son yıllarda bulut sağlayıcıları ve ambar
ürünlerinin ortak zemini hâline geldi (AWS S3 Tables, Snowflake ve Databricks desteği).

| Gerekir | Gerekmez |
|---|---|
| Aynı tabloya birden çok yazar | Tek yazar |
| Satır güncelleme/silme (örn. KVKK/GDPR "unutulma hakkı" talebi) | Sadece ekleme (append-only) |
| Zaman içinde geriye bakma (time travel) | Küçük veri, basit akış |
| Sık şema veya partition değişimi | Şema oturmuş |

### 6.3 Göl mü ambar mı — ve lakehouse

| | **Veri gölü (lake)** | **Veri ambarı (warehouse)** | **Lakehouse** |
|---|---|---|---|
| Depolama | Açık format, senin nesne deponda | Ürünün kendi iç formatı | Açık format + tablo formatı |
| Motor | Ayrı seçilir (Trino, Spark, DuckDB) | Ürünle gelir | Ayrı seçilebilir |
| Şema | Okurken uygulanır | Yazarken zorunlu | Tablo formatıyla zorunlu |
| Kilitlenme | Düşük | **Yüksek** | Düşük |
| Kullanım kolaylığı | Düşük — kendin monte edersin | **Yüksek** | Orta |

> **Açık format seçmek stratejik bir karardır:** verin Parquet + Iceberg olarak kendi S3
> kovanda duruyorsa, motoru değiştirmek verini taşımadan mümkündür. Ambarın iç formatına
> girmiş veri o ambara bağlıdır.

---

## 7. İşleme motorları

| Motor | Ölçek | Ne zaman |
|---|---|---|
| pandas | Tek makine, bellekte | < 1 GB, keşif |
| **polars** | Tek makine, çok çekirdek | 1–100 GB, DataFrame API |
| **DuckDB** | Tek makine, sütunlu, SQL | 1–100 GB+, SQL. Parquet'i doğrudan okur |
| **PySpark** | Dağıtık | TB ölçeği, ağır join, streaming |
| **Trino** | Dağıtık **sorgu** motoru | Farklı kaynakları tek SQL ile sorgulamak (federasyon). Depolamayı yönetmez |
| **ClickHouse** | Sütunlu OLAP veritabanı | Çok hızlı analitik sorgu, gerçek zamanlıya yakın panolar |
| Druid / Pinot / StarRocks | Gerçek zamanlı OLAP | Akış verisi üzerinde saniye altı sorgu |
| Snowflake / BigQuery | Ambar (depolama + motor) | SQL öncelikli analitik, altyapı yönetmeden |

### Spark ne zaman gerekir — tek soru

**Veri tek makineye sığıyor mu?**

| Spark kullan | Spark kullanma |
|---|---|
| Veri tek makineye sığmıyor | Verin 10 GB — polars/DuckDB hem daha hızlı hem daha basit |
| Organizasyon zaten Databricks/EMR üzerinde | Sadece CV'de dursun diye |
| Spark Structured Streaming gerekiyor | Tek tablo, tek dönüşüm |
| Çok kaynaklı, çok büyük join | |

Spark'ın **sabit maliyeti** vardır: JVM açılışı, cluster provisioning, shuffle. Küçük
işlerde bu maliyet işin kendisinden büyüktür. Junior'ların en sık yaptığı fazla mühendislik
tam burasıdır.

---

## 8. Orkestrasyon

| Araç | Model | Ne zaman |
|---|---|---|
| **cron** | Tek makine, tek komut | Tek iş, bağımlılık yok. Küçükse **meşru bir cevaptır** |
| EventBridge + Lambda / Step Functions | AWS-native, sunucusuz | AWS'desin, akış basit |
| **Airflow** | **Görev** odaklı, en yaygın, olgun | Karmaşık bağımlılıklar, büyük ekip, geniş konnektör ekosistemi |
| **Dagster** | **Varlık** odaklı, tip ve sözleşme desteği | Tabloları merkeze alan modern yaklaşım, güçlü yerel geliştirme |
| **Prefect** | Python odaklı, hafif | Python ağırlıklı akışlar |
| Kestra / Mage | Bildirimsel / notebook odaklı | Daha yeni alternatifler |
| Argo Workflows | Kubernetes-native | Zaten K8s üzerindeysen |

### Görev odaklı ↔ varlık odaklı — kavramsal ve önemli

- **Airflow sorar:** *"hangi görevler, hangi sırayla çalışacak?"*
- **Dagster sorar:** *"hangi tablolar var, her birini ne üretiyor?"*

İkincisi veri mühendisliğinin gerçek sorusuna daha yakındır, çünkü sonunda bakımını
yaptığın şey görevler değil **tablolardır**. "DAG yeşil ama tablo boş" durumu görev odaklı
sistemlerin klasik kör noktasıdır.

### Orkestratörün gerçekten yaptığı iş

Zamanlama en az önemli kısmıdır. Asıl değeri: **bağımlılık sırası**, **yeniden deneme**,
**geri doldurma (backfill)**, **eşzamanlılık kontrolü**, **hata bildirimi**, **çalışma
geçmişi**. Bunlara ihtiyacın yoksa cron yeterlidir ve bunu söylemek utanılacak bir şey
değildir.

---

## 9. Veri kalitesi ve gözlemlenebilirlik

Atlanan ama profesyonel bir platformda **taşıyıcı** olan katman. Boru hattının çalışması
verinin doğru olduğu anlamına gelmez.

### İki farklı soru

| Soru | Alan | Araçlar |
|---|---|---|
| **Boru hattı çalıştı mı?** | Pipeline gözlemlenebilirliği | Orkestratör log'ları, metrikler, alarm |
| **Veri doğru mu?** | Veri kalitesi | dbt tests, Great Expectations, Soda |

İkisi bağımsızdır: iş yeşil bitip tabloya sıfır satır yazılmış olabilir. Bu, "sessiz
başarısızlık" denen ve en pahalıya patlayan durumdur.

### Test tipleri

| Tip | Örnek |
|---|---|
| **Şema** | Kolon var mı, tipi doğru mu |
| **Tekillik** | Primary key gerçekten tekil mi |
| **Doluluk** | `NOT NULL` beklenen kolonda null var mı |
| **Aralık** | `playcount` negatif mi |
| **Referans bütünlüğü** | Yabancı anahtar karşılığı var mı |
| **Hacim / anomali** | Satır sayısı dünkünün %10'u mu geldi |
| **Tazelik (freshness)** | En son kayıt kaç saatlik |

Son ikisi en çok gerçek olayı yakalayanlardır ve genelde en son yazılırlar.

| Araç | Not |
|---|---|
| **dbt tests** | dbt kullanıyorsan bedava gelir; `unique`, `not_null`, `accepted_values`, `relationships` |
| **Great Expectations** | Bağımsız, güçlü, kurulum yükü var |
| **Soda Core** | YAML ile bildirimsel kalite kontrolleri |
| **Elementary** | dbt üzerine anomali tespiti ve raporlama |
| **OpenLineage / Marquez** | Lineage için açık standart |
| Monte Carlo, Bigeye, Metaplane | Yönetilen "veri gözlemlenebilirliği" ürünleri |

> Bu projede kalite katmanı **pytest + fixture** olarak başlıyor (Adım 7). Sektörde bunun
> üstüne üretim verisi üzerinde çalışan kontroller eklenir — test kodu doğrular, kalite
> kontrolü **veriyi** doğrular. İkisi farklı şeydir.

---

## 10. Katalog ve yönetişim

Katalog, *"S3'te şu prefix'te Parquet dosyaları var"* bilgisini *"şu şemaya sahip şu tablo"*
bilgisine çeviren yerdir. Athena, Redshift Spectrum, EMR, Spark ve Trino bunu okur.
Katalog olmadan bir SQL motoru S3'teki dosyaların ne olduğunu bilmez.

| Araç | Rol |
|---|---|
| **Hive Metastore** | Klasik teknik metastore; hâlâ birçok şeyin altında |
| **AWS Glue Data Catalog** | AWS'nin metastore'u; Athena bunu okur |
| **Unity Catalog** | Databricks; teknik metadata + erişim yönetimi |
| **Apache Polaris** | Iceberg için açık REST katalog |
| **DataHub / OpenMetadata / Amundsen** | Keşif katalogları: arama, sahiplik, lineage, doküman |
| Atlan / Collibra / Alation | Kurumsal yönetişim ürünleri |

**İki farklı "katalog" var, karıştırılır:**

| Tip | Kime hizmet eder | Örnek |
|---|---|---|
| **Teknik metastore** | Sorgu motoruna — şema, konum, partition | Glue Catalog, Hive Metastore |
| **Keşif kataloğu** | İnsana — bu tablo ne, kim sahibi, nereden geliyor | DataHub, Atlan |

### Glue tek bir ürün değildir

| Bileşen | Ne yapar | Ne zaman |
|---|---|---|
| **Glue Data Catalog** | S3 dosyalarını tablo olarak kaydeder | Athena / Spectrum / EMR kullanacaksan neredeyse her zaman |
| **Glue ETL** | Yönetilen Spark, cluster kurmadan | AWS'de Spark gerekiyorsa |
| **Glue Crawler** | S3'e bakıp şemayı **tahmin eder** | Kolay, ama tipleri sık yanlış çıkarır ve partition karmaşası yaratır. Şemayı bilen ekipler tabloyu elle tanımlar |

---

## 11. Streaming — batch dışı dünya

| Katman | Araçlar |
|---|---|
| **Mesaj taşıma** | Apache Kafka, AWS Kinesis, Google Pub/Sub, Azure Event Hubs, Redpanda, Pulsar |
| **Akış işleme** | Apache Flink, Spark Structured Streaming, Kafka Streams |
| **Streaming veritabanı** | Materialize, RisingWave — sonucu artımlı olarak günceller |
| **Gerçek zamanlı OLAP** | Druid, Pinot, ClickHouse |

### Streaming ne zaman gerekir

Tek soru: **veri kaç saniye/dakika/saat eski olabilir?**

| Kabul edilen gecikme | Doğru yaklaşım |
|---|---|
| Saatler / gün | **Batch.** Bu projede olduğu gibi |
| Dakikalar | Sık batch (mikro-batch) — genelde yeterli ve çok daha basit |
| Saniyeler | Gerçek streaming |

**Streaming'in gizli maliyeti:** durum yönetimi, geç gelen olaylar, tam-bir-kez semantiği,
yeniden oynatma, pencereleme. Batch'te önemsiz olan her şey streaming'de bir tasarım
kararına dönüşür. "Gerçek zamanlı olsun" isteği genelde ölçülmemiş bir istektir —
sorulacak soru: *"bu veriyi kim, ne sıklıkta, hangi kararı vermek için okuyacak?"*

---

## 12. Serve: BI ve reverse ETL

| Kategori | Araçlar | Not |
|---|---|---|
| **BI / görselleştirme** | Looker, Power BI, Tableau, Metabase, Superset, Lightdash, Hex, Omni | Metabase ve Superset açık kaynak |
| **Semantik katman** | dbt Semantic Layer, Cube | Metrik tanımını tek yerde tutar — "aktif kullanıcı" her panoda aynı şey olsun diye |
| **Reverse ETL** | Hightouch, Census | Ambardaki veriyi **geri** operasyonel sistemlere (CRM, reklam) yazar |
| **Notebook / ad-hoc** | Jupyter, Hex, Deepnote | Keşif |

**Semantik katman neyi çözer:** aynı metriğin beş panoda beş farklı SQL'le hesaplanması ve
beş farklı sayı çıkması. Bu, veri ekiplerinin en çok zaman kaybettiği tartışmadır.

---

## 13. Altyapı ve dağıtım

| Alan | Araçlar |
|---|---|
| **IaC** | Terraform, Pulumi, AWS CDK, CloudFormation |
| **Paketleme** | Docker |
| **Çalıştırma** | Kubernetes, ECS, Lambda, Cloud Run |
| **CI/CD** | GitHub Actions, GitLab CI |
| **Secret yönetimi** | AWS Secrets Manager, HashiCorp Vault, SOPS |
| **Kod kalitesi** | ruff, mypy, pytest, pre-commit |

> Son satır bu projenin 0. adımıdır. Sektörde bu katman tartışma konusu bile değildir —
> olmadığı repo "prototip" sayılır.

---

## 14. Bulut karşılıkları matrisi

| İşlev | AWS | GCP | Azure |
|---|---|---|---|
| Nesne depolama | **S3** | Cloud Storage | ADLS Gen2 |
| Veri ambarı | Redshift | **BigQuery** | Synapse / Fabric |
| Göl üzerinde SQL | **Athena** | BigQuery external / BigLake | Synapse Serverless |
| Yönetilen Spark | EMR, Glue ETL | Dataproc | Synapse Spark |
| Teknik katalog | **Glue Data Catalog**, S3 Tables | Dataplex | Purview |
| Orkestrasyon | MWAA, Step Functions | Cloud Composer | Data Factory |
| Sunucusuz hesap | **Lambda** | Cloud Run / Functions | Functions |
| Zamanlayıcı | **EventBridge** | Cloud Scheduler | Logic Apps |
| Akış taşıma | Kinesis, MSK | Pub/Sub | Event Hubs |
| Akış işleme | Managed Flink | Dataflow (Beam) | Stream Analytics |
| Yönetilen ingest / CDC | DMS, AppFlow | Datastream | Data Factory |
| Secret | Secrets Manager | Secret Manager | Key Vault |

**Databricks ve Snowflake üç bulutta da çalışır** — bulut seçiminden bağımsızdırlar.
Kalın yazılanlar bu projede kullanılacak olanlar.

---

## 15. Boyut sezgisi — en işe yarar tek kural

| Tek işin veri boyutu | Doğru araç |
|---|---|
| < 1 GB | pandas, hatta saf Python |
| 1–100 GB | **polars / DuckDB** — tek makine, çok hızlı |
| 100 GB – birkaç TB | DuckDB (büyük makine) veya Spark; sınır bulanık |
| > birkaç TB, veya çok kaynaklı ağır join | **Spark** |

**Yanılmanın bedeli asimetriktir.** pandas'ta kalıp gece 3'te bellek hatası almak can
sıkıcıdır ama düzeltilebilir. Gereksiz yere Spark'a geçmek ise kalıcı karmaşıklık, maliyet
ve işe alım kısıtı yaratır.

> Yukarı göç etmek, aşağı inmekten kolaydır. Şüphedeysen küçük araçtan başla.

---

## 16. Maliyet modelleri — bu, tasarımı değiştirir

Az öğretilen ama mimariyi doğrudan belirleyen konu.

| Sistem | Neyi faturalar | Tasarıma etkisi |
|---|---|---|
| Snowflake | Warehouse çalışma süresi (saniye) | Boşta duran warehouse para yakar → `auto-suspend` şart |
| BigQuery (on-demand) | **Taranan bayt** | Partition ve cluster **doğrudan para** |
| **Athena** | **Taranan bayt** | Aynı. Partition etmemek faturayı katlar |
| Databricks | DBU (hesap birimi) × süre | Cluster boyutu ve auto-termination |
| Lambda | GB-saniye | Bellek ayarı hem hızı hem maliyeti değiştirir |
| EMR / Glue ETL | Instance-saat / DPU-saat | Boşta cluster = para |
| S3 | Depolama **+ istek sayısı** | Çok sayıda küçük dosya = çok istek = para **ve** yavaşlık |
| Fivetran | Değişen satır sayısı (MAR) | Gürültülü kaynak faturayı patlatır |

**İki kritik sonuç:**

> **1.** Taranan bayt üzerinden faturalanan bir motorda **partition'lamak bir performans
> ayarı değil, bir maliyet kararıdır.** Sorgudaki filtre partition'a denk gelmiyorsa tüm
> tabloyu tararsın ve tüm tablo kadar ödersin.

> **2. Küçük dosya problemi:** çok sayıda ufak Parquet dosyası hem S3 istek maliyetini
> artırır hem sorguyu yavaşlatır — her dosya için ayrı metadata okuması gerekir. Çözümü
> periyodik **compaction** (birleştirme).

---

## 17. Karar sırası — hangi soru önce

1. **Veri ne kadar, ne hızda büyüyor?** → motoru bu belirler
2. **Ne kadar taze olmalı?** → batch mi streaming mi
3. **Kim sorgulayacak, hangi dille?** → ambar mı, göl + sorgu motoru mu
4. **Dönüşüm SQL mi Python mu?** → dbt mi, değil mi
5. **Kaç kaynak, bağımlılık var mı?** → orkestratör gerekli mi, cron yeter mi
6. **Faturalama modeli ne?** → partition ve dosya boyutu stratejisi
7. **Bakımını kim yapacak?** → ekibin işletemediği en iyi araç, yanlış araçtır

7. madde en çok göz ardı edilenidir ve gerçek bir kısıttır. Tek kişilik bir ekipte Airflow
kurmak, çözdüğünden fazla sorun yaratır.

---

## 18. Bu projede: ROADMAP adımı → araç kategorisi

Günde ~100 satır, yılda ~36 bin satır (ADR-0006).

| Adım | Katman | Bu projede | Sektördeki karşılığı |
|---|---|---|---|
| **0** Repo | Altyapı | uv, git, ruff, mypy, pytest | Aynı — bu katman tartışmasız |
| **1** Veriyi tanı | — | Elle keşif, ölçüm, grain, şema | **Karşılığı yok.** Hiçbir araç bunu yapmaz |
| **2** Config | Config / secret | `pydantic-settings`, `.env` | + Secrets Manager, Vault, dlt config |
| **3** Extract | Ingestion | `httpx` elle + retry + sayfalama | **dlt**, Airbyte, Fivetran |
| **4** Raw katman | Depolama + format | Yerel/S3 + Parquet | + Iceberg/Delta tablo formatı |
| **5** Transform | Dönüşüm | polars/pandas + Pydantic | **dbt** (SQL yolu) veya polars/Spark (Python yolu) |
| **6** Orkestrasyon | Orkestrasyon | EventBridge + Lambda | **Airflow**, **Dagster**, Prefect |
| **7** Test | Kalite | pytest + fixture | + Great Expectations, Soda, dbt tests, freshness/hacim kontrolleri |
| **8** CI | Altyapı | GitHub Actions | Aynı + Terraform |
| **9** AWS | Bulut | S3, Lambda, EventBridge, Athena, Glue Catalog | + IaC, monitoring, alarm |

### Bu projede kullanılmayacaklar ve neden

| Araç | Neden değil |
|---|---|
| PySpark | 10 yılda 365 bin satır. Sabit maliyeti işin kendisinden büyük |
| Snowflake / BigQuery | Tek tüketici, gereksiz ve ücretli |
| Iceberg / Delta | Tek yazar, append-only, küçük. Düz partition'lı Parquet yeterli |
| Glue Crawler | Şemayı 1.7'de **elle** tanımladık; tahmin ettirmenin anlamı yok |
| Airflow / Dagster | 6. adımda tek iş var |
| dbt | **Sınırda.** Tek tabloyla hayır; `playcount` farkından günlük artış türeten ikinci bir model gelirse mantıklı olur |
| Streaming | Chart günde bir kez anlamlı değişiyor |

### Bekleyen problem

Günde bir küçük Parquet dosyası, 3 yılda ~1000 minik dosya eder. Athena her dosya için ayrı
metadata okur. **Compaction** 6. veya 9. adımda gündeme gelecek. Şimdi çözülecek bir sorun
değil ama **beklenen** bir sorun.

---

## 19. Junior tuzakları

| Tuzak | Neden yanlış |
|---|---|
| **CV odaklı araç seçimi** | Mülakatta ikinci soru hep aynı: "neden bunu seçtin?" |
| Spark'a çok erken geçmek | Sabit maliyet işten büyük; karmaşıklık kalıcı |
| **dbt'yi bir motor sanmak** | dbt hesap yapmaz, SQL üretip motora gönderir |
| ETL ile ELT'yi karıştırmak | Ham veriyi saklamamak, dönüşüm hatasını geri alınamaz yapar |
| Sorgu tabanlı çekimi CDC sanmak | Silinen satırları göremezsin |
| Satır satır `INSERT` | Her hedefin toplu yükleme yolu var, 10–100 kat fark |
| Crawler'ın çıkardığı şemaya güvenmek | Tipleri sık yanlış çıkarır |
| Partition'lamayı performans ayarı sanmak | Taranan bayt faturalayan motorlarda doğrudan maliyet |
| Orkestratörü ilk gün kurmak | Tek iş varken cron meşru bir cevaptır |
| "Gerçek zamanlı olsun" demek | Ölçülmemiş istek. Önce sor: bu veriyi kim, ne sıklıkta, hangi kararı vermek için okuyacak |
| Testi "kod doğru mu" sanmak | Kod testi ayrı, **veri** kalitesi ayrı. İş yeşil bitip tablo boş olabilir |
| CSV ile analitik depolama | Tipsiz, sıkıştırmasız, sütunsuz |

---

## 20. Mülakat

**"ETL mi ELT mi kullanırsın, neden?"**

> Varsayılanım ELT. Ham veriyi hedefte sakladığım için dönüşümü yanlış yaptığımda yeniden
> işleyebilirim; ETL'de dönüşüm yüklemeden önce olduğu için hata geri alınamaz ve kaynağı
> yeniden çekmem gerekir — çekilemiyorsa kayıptır. İstisna PII: kişisel veriyi ambara hiç
> sokmamam gerekiyorsa yüklemeden önce maskelerim, yani EtLT olur.

**"dbt ile Snowflake arasındaki fark ne?"**

> Farklı katmanlar. Snowflake bir ambar — depolama, motor ve katalog bir arada. dbt bir
> dönüşüm çerçevesi: veriye dokunmaz, SQL üretir ve bir motora gönderir. dbt'yi
> Snowflake'in, BigQuery'nin veya DuckDB'nin üstünde çalıştırabilirsin.

**"Neden Spark kullanmadın?"**

> Veri günde 100 satır, yılda 36 bin. Spark'ın sabit maliyeti — JVM açılışı, cluster
> provisioning, shuffle — işin kendisinden büyük olurdu. Parquet + DuckDB seçtim. Geçiş
> eşiğim de belli: veri tek makineye sığmamaya başladığında Spark'a geçerim.

**"Kaynak veritabanından silinen satırları nasıl yakalarsın?"**

> Sorgu tabanlı çekimle yakalayamam — `WHERE updated_at > x` silinmiş satırı göremez.
> Log tabanlı CDC gerekir: Debezium ile binlog veya WAL okunur. CDC'nin var olma sebebi
> tam olarak budur.

**"Athena'da maliyeti nasıl kontrol edersin?"**

> Athena taranan bayt üzerinden faturalanır, dolayısıyla partition tasarımı bir maliyet
> kararıdır. Sorgularda kullanılan filtre kolonunu partition anahtarı yaparım — bu projede
> `snapshot_date`. Sütunlu format kullanırım ki gereksiz kolonlar taranmasın, ve küçük
> dosya birikmesine karşı periyodik compaction planlarım.

---

## 21. Sözlük

| Terim | Anlamı |
|---|---|
| **ETL / ELT** | Dönüşümün yüklemeden önce mi sonra mı yapıldığı |
| **CDC** | Change Data Capture — veritabanı log'undan değişiklikleri okumak |
| **veri ambarı (warehouse)** | Depolama + motor + katalogu birlikte sunan yönetilen sistem |
| **veri gölü (lake)** | Ham dosyaların açık formatlarda durduğu depolama |
| **lakehouse** | Göl üzerine tablo formatı koyarak ambar özellikleri kazandırma |
| **tablo formatı** | Parquet dosyalarına ACID, time travel, şema evrimi ekleyen metadata katmanı |
| **katalog / metastore** | Dosyaların hangi tabloya, hangi şemayla karşılık geldiği kaydı |
| **sütunlu (columnar)** | Verinin kolon kolon saklanması; analitik okumada çok daha hızlı |
| **shuffle** | Dağıtık motorda verinin makineler arası yeniden dağıtılması — en pahalı işlem |
| **compaction** | Çok sayıda küçük dosyayı daha az sayıda büyük dosyaya birleştirme |
| **incremental model** | Tüm tabloyu değil, yalnızca yeni/değişen kısmı işleyen dönüşüm |
| **upsert / merge** | Anahtara göre varsa güncelle, yoksa ekle |
| **SCD Type 1 / 2** | Değişimde üzerine yaz (1) veya yeni satır açıp geçmişi koru (2) |
| **backfill** | Geçmiş bir dönem için boru hattını sonradan çalıştırmak |
| **lineage** | Bir tablonun hangi kaynaklardan, hangi adımlardan türediğinin izi |
| **freshness** | Verinin ne kadar güncel olduğu; en sık kullanılan kalite kontrolü |
| **semantik katman** | Metrik tanımlarının tek merkezde tutulduğu katman |
| **reverse ETL** | Ambardaki veriyi operasyonel sistemlere geri yazmak |
| **görev / varlık odaklı** | Orkestratörün "ne çalışır" mı "ne var" mı sorusunu merkeze alması |
| **MAR** | Monthly Active Rows — bazı ingestion ürünlerinin faturalama birimi |

---

## Güncelleme kaydı

| Tarih | Ne değişti |
|---|---|
| 2026-08-13 | İlk sürüm — katman haritası, boyut eşikleri, maliyet modelleri |
| 2026-08-13 | Yeniden yazıldı: E/L/T ekseni eklendi, ETL↔ELT ayrımı, CDC, yükleme stratejileri, veri kalitesi, katalog, streaming, serve, bulut matrisi, ROADMAP eşlemesi |

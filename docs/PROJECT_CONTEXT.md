# Proje Bağlamı — Last.fm ETL Pipeline

Bu dosya projenin **sabit sözleşmesidir**: hedef, tercihler, mimari. Nadiren değişir.

> **Güncel durum bu dosyada değildir.** Nerede kaldığımız için → [`PROGRESS.md`](PROGRESS.md)
> **Detaylı plan da bu dosyada değildir.** Alt adımlar için → [`ROADMAP.md`](ROADMAP.md)
> Aynı bilgiyi iki yerde tutmak = iki gerçek = kaçınılmaz sapma.

---

## 1. Ben kimim, ne istiyorum

**Barış.** Data engineering öğreniyorum. Python'a hakimim sayılır ama pipeline mimarisi,
veri kalitesi, idempotency gibi konularda tecrübem yok.

**Amaç:** Öğrenme + portfolyo. Sonunda GitHub'da durabilecek, mülakatta anlatabileceğim,
**gerçekten uçtan uca çalışan** bir pipeline istiyorum.

**Bu projenin kökeni.** DataVidhya "Spotify Pipeline" dersinin **dört parçasını**
uyguluyorum:

| Ders | Konu |
|---|---|
| P1 | Mimari, API kimlik bilgileri, AWS servisleri, S3 bucket'ları |
| P2 | Local Python: extract + nested JSON'u tablolara düzleştir |
| P3 | İki Lambda, layer, env var, CloudWatch + S3 tetikleyicileri, IAM |
| P4 | Glue Crawler, Data Catalog, Athena SQL |

Kursun versiyonu kasten basit: kimlik bilgileri kodda yazılı, kod Lambda konsol
editörüne yapıştırılıyor, `src/` yok, `.env`/`.venv` yok, test yok, paketleme yok,
IAM `AmazonS3FullAccess`. **Claude ile çalışmamın sebebi tam olarak bu boşluk** — bir
profesyonelin aynı mimariyi baştan sona nasıl kuracağını öğrenmek.

**Kritik kısıt: kapsam kurstur — ne eksik, ne fazla.** Öğrenmek istediğim şey
mimarinin kendisi değil, *etrafındaki yapı*: dizin düzeni, config ve sır yönetimi,
hata yolları, test, paketleme, IAM, maliyet. Kursta olmayan ve bu listede de olmayan
her şey `ROADMAP.md` → "Sonraki tur". Gerekçe: ADR-0010.

**Öğrenme tarzım:** Adım adım, açıklaya açıklaya. **Kodu ben yazarım.** Claude `src/`
altına dosya oluşturmaz; sohbette gösterir, ben yazarım.

### Geçmiş deneyim — tekrarlamak istemediğim hatalar

**Not: Aşağıdaki proje terk edildi. Kodu kullanılmayacak, sadece ders listesi.**

Bir Spotify ETL projesine başlamıştım. Spotify API'de aradığım veriye ulaşamayınca
(audio features endpoint'i kısıtlandı, playlist verisi yetersiz kaldı) Last.fm'e geçtim.

- ✅ JSON formatında yapılandırılmış loglama kurdum
- ✅ Config sınıfında `__post_init__` ile doğrulama yaptım
- ✅ `raise_for_status()`, `timeout`, hatayı loglayıp yeniden `raise` etme
- ❌ Pipeline hiç uçtan uca çalışmadı — `main.py` metodu çağırmadan "başarılı" logladı
- ❌ Transform ve load katmanı hiç yazılmadı
- ❌ Test yok, paketleme yok, CI yok
- ❌ `__pycache__` ve log dosyaları git'e commit edilmişti

Bu sefer **dar ama uçtan uca çalışan** bir dilimle başlamak istiyorum. Boş ama güzel bir
klasör yapısı değil.

---

## 1b. Çalışma anlaşması

> Bu bölüm 2026-08-15'te eklendi. Sebebi §1'deki hatanın **farklı bir kılıkta tekrar
> etmesi**: geçmiş projede boş bir klasör yapısı vardı, bu projede dolu bir doküman
> klasörü. İkisinde de çalışan pipeline yoktu.

**Ölçüm:** 9 günde 31 commit, 9.527 satır doküman, 0 satır pipeline kodu.

**Teşhis:** Doküman kötü değildi — ADR-0005'in grain analizi ve not 17'nin rate limit
protokolü gerçek iş. Sorun **sıra**: doküman koddan önce yazılıyordu. Uygulanmamış
bilgi dondurulunca iki şey oluyor:

1. Yanlış olduğu anlaşılmıyor. `PROJECT_CONTEXT.md` bir süre "Last.fm hatada bile
   HTTP 200 döner" dedi. Ölçüm bunu çürüttü (1.3).
2. Karar, dayandığı ölçüm olmadan veriliyor. ADR-0007 (dlt) 0 satır kod varken
   yazıldı; ADR-0008 aynı gün onu kısmen geçersiz kıldı; ADR-0009 ikisini de
   supersede etti. Üç ADR, sıfır çalışan kod.

**Anlaşma:**

| Konu | Kural |
|---|---|
| Not | Adım **çalıştıktan sonra** yazılır. Uzunluk serbest. Hiçbir adımı bloklamaz |
| ADR | Sadece geri alması pahalı kararlar için. `git revert` yetiyorsa commit mesajıdır |
| Alt adım bütçesi | 14. Yeni alt adım ancak bir eskisi silinerek eklenir |
| Adım süresi | İki oturumu aşarsa kapsam şişmiştir — alt adım kesilir |
| Araç | Bu turda yeni araç yok. Araç, veriden sonra öğrenilir |
| Kapsam şişmesi | "Şunu da ekleyelim" cümlesi bir uyarıdır. Aday `ROADMAP.md`'nin "Sonraki tur" bölümüne yazılır, plana değil |

**Claude'un görevi bu anlaşmayı korumak.** Kapsam şişerse, üç alt adım tek mesajda
anlatılırsa veya bir not koddan önce yazılmaya başlanırsa — durdurulur.

---

## 1c. Çalışma anlaşması — 2026-08-20 revizyonu: hız modu

> §1b teşhisi doğruydu ama tedavi yetmedi. 2026-08-20 itibarıyla: 35+ commit,
> ~10.000 satır doküman, **63 satır** pipeline kodu ve o kod hâlâ bir kez
> çalıştırılmamış. Barış'ın kendi ifadesi: *"çok geç kaldım, artık elimde çalışan
> bir pipeline olsun."* Bu bir kapsam kararı değil, bir **öncelik** kararıdır.

**Değişen iki kural:**

| Eski | Yeni | Gerekçe |
|---|---|---|
| Claude `src/` altına dokunmaz; Barış yazar | **Claude yazar, Barış review eder ve çalıştırır** | Yazma hızı darboğazdı. Öğrenme `docs/annotated/` aynasından devam ediyor |
| Bir şeyi açıklamadan önce Barış'a soru sorulur | **Tahmin sorusu sorulmaz.** Doğrudan anlatılır | Tahmin turu tur başına 1 mesaj ekliyordu ve ilerlemeyi bloke ediyordu |

**Eklenen kural — terim borcu (2026-08-20):**

> Claude bir terimi **ilk kez** kullandığında, aynı cümlede veya hemen ardından
> tanımını verir. İstisna yok: "bucket", "shell", "runtime", "layer", "role",
> "handler", "prefix" — hepsi tanımlanır.

Tetikleyen olay: `bucket` ve `bash` terimleri, tanımlanmadan onlarca kez kullanıldı.
Barış'ın ifadesi: *"hâlâ benim bucket'ın ne olduğunu bildiğimi varsayıyorsun."*

Kuralın iki kenarı:

- **Yeni dosya açılmaz.** Terimler sözlüğü diye ayrı bir not **yazılmayacak** —
  bu proje zaten doküman fazlasından muzdarip. Tanım geçtiği yerde verilir;
  kalıcı olması gerekiyorsa ilgili `docs/annotated/` aynasına veya mevcut bir nota girer.
- **Tanım kısa olur.** Bir cümle + gerekiyorsa bir benzetme. Paragraf değil.

**Değişmeyenler — bunlar hız modunda da geçerli:**

- **Kodu Barış çalıştırır.** Claude'un yazdığı hiçbir dosya, Barış kendi makinesinde
  çalıştırıp çıktısını görmeden "bitti" sayılmaz. Ölçülmemiş kod, yazılmamış koddur.
- **Commit'i Barış atar.** Diff okunmadan commit atılmaz; review buradan yapılır.
- **Her yeni `.py` dosyasının aynası aynı commit'te yazılır** (`docs/annotated/`).
  Ayna artık ders kitabının kendisi — kod Claude'dan geliyorsa ayna daha da önemli.
- **Tek seferde tek alt adım.** Hız, adım atlamak değil, adım başına mesaj sayısını
  azaltmak demektir.
- **Kapsam şişmesi yasağı.** "Şunu da ekleyelim" hâlâ durdurulur.

**Rota kararı (aynı gün):** ROADMAP sırası **bozulmuyor**. P1.1 kapanır → P1.2 (IAM +
budget alarm) → P1.3 (S3 bucket'lar) → P2 (extract/transform). "Önce local uçtan uca,
AWS sonra" seçeneği değerlendirildi ve **reddedildi**; P2.2 raw'ı S3'e yazıyor,
bucket'sız P2 yarım kalırdı.

---

## 1d. Çalışma anlaşması — 2026-08-22: **karma mod** (yürürlükteki kural)

§1c'nin "Claude yazar" kuralı P2'ye gelindiğinde fazla geniş bulundu. Barış'ın ifadesi:
*"şimdi tüm kodu sen yazarsan anlamayabilirim, ama her şeyi de ben yazamam."*

**Kural: Claude iskeleti yazar, Barış gövdeyi doldurur.**

| Claude yazar | Barış yazar |
|---|---|
| Dosya ve modül yapısı, sorumluluk sınırı | **Fonksiyon gövdeleri** |
| Fonksiyon **imzaları**: ad, parametreler, type hint, dönüş tipi | Kontrol akışı: `if`, döngü, `try` blokları |
| Docstring'ler — fonksiyonun sözleşmesi | Gerçek mantık |
| Sabitler, `Enum`'lar, exception sınıf hiyerarşisi | |
| Gövde yerine `# TODO(barış):` + ne yapılacağının tarifi | |

**Akış:** Claude iskeleti `src/` altına yazar → sohbette her bloğun neden öyle olduğunu
anlatır → Barış gövdeleri doldurur → çalıştırır → takılırsa Claude **önce ipucu** verir,
cevabı değil → çalışınca Claude `docs/annotated/` aynasını yazar → Barış commit'ler.

**Ayna en sonda yazılır**, iskelet aşamasında değil: yarım kodun aynası yanlış bilgi taşır.

**İskeletin ölçüsü:** İskelet çalıştırılabilir olmalı (import edilebilir, `NotImplementedError`
fırlatsa bile), ama iş mantığı içermemeli. Bir fonksiyonun gövdesi tek satırsa ve o satır
mantığın kendisiyse, o satır Claude'a değil Barış'a aittir.

**Değişmeyen:** §1c'deki "değişmeyenler" listesi aynen geçerli — kodu Barış çalıştırır,
commit'i Barış atar, ayna aynı commit'te gelir, tek seferde tek alt adım, kapsam şişmesi yok.

> **Not:** bu bölüm reponun kaydıdır. Claude'un davranışını asıl belirleyen metin
> Claude projesinin **instructions** alanıdır; oradaki "src/'e dokunma" ve "önce soru
> sor" maddeleri de elle güncellenmelidir, yoksa yeni oturum eski kurala döner.

---

## 2. Teknik tercihler

| Konu | Karar |
|---|---|
| Sohbet dili | Türkçe |
| Kod / docstring / commit / README / ADR dili | İngilizce |
| `docs/notes/` dili | Türkçe (öğrenme defteri) |
| Python | **3.14** (`>=3.14,<3.15`) — AWS Lambda `python3.14` runtime'ıyla eşlendi (2026-08-20). Derlenmiş wheel'ler minor sürüme bağlı olduğu için üst sınır bir tercih değil, deploy hedefi |
| Paket yönetimi | `uv`, project mode (ADR-0003) |
| HTTP | `requests` — elle yazılan client, retry ve backoff dahil |
| Transform | `pandas` (düzleştirme, dedupe) + `pyarrow` (Parquet). **Framework yok** (ADR-0009) |
| AWS SDK | `boto3` |
| Kapsam | Kursun dört parçası (ADR-0010). Local'de yaz ve doğrula → **aynı fonksiyonları** Lambda'ya taşı |
| Bulut | AWS: S3 (×2 bucket), Lambda (×2), EventBridge, Glue Crawler + Data Catalog, Athena |
| Depo formatı | Raw: **JSON** (hiç dokunulmamış) — Transformed: **Parquet** |
| Tablolar | `tracks` ve `artists` — **iki tablo**. `chart.getTopTracks` album döndürmüyor |
| IaC | Yok. Konsol + `boto3`. Terraform sonraki tur |

**Bilinçli olarak kullanılmayanlar:** dlt, dbt, DuckDB, Docker, mypy, pre-commit,
Airflow. Gerekçeler ADR-0009, ADR-0010 ve `ROADMAP.md` → "Sonraki tur"da.

---

## 3. Veri kaynağı: Last.fm API

**Base URL:** `http://ws.audioscrobbler.com/2.0/`
**Dokümantasyon:** https://www.last.fm/api

### Spotify'dan farkları

| | Spotify | Last.fm |
|---|---|---|
| Auth | OAuth, token süresi dolar | Sadece `api_key` query parametresi |
| Endpoint | Kaynak başına ayrı URL | **Tek URL**, `method` parametresi değişir |
| Varsayılan format | JSON | **XML** — `format=json` göndermek zorunlu |
| Hata davranışı | HTTP status kodu doğru | Status **ve** gövde birlikte hata taşır |

### İki kritik tuzak

1. **`format=json` unutulursa** → XML döner, `response.json()` patlar.
2. **Hata iki katmanda birden gelir** → HTTP status *ve* gövdedeki `error` kodu.
   Adım 1.3'te ölçüldü (tahmin değil):

   | Deney | Status | Gövde |
   |---|---|---|
   | Bozuk `api_key` | `403` | `{"message":"Invalid API key...","error":10}` |
   | Bozuk `method` | `400` | `{"message":"Invalid Method...","error":3}` |

   **Düzeltme kaydı:** bu dosyanın önceki hâli "hatada bile HTTP 200 döner" diyordu.
   Ölçüm bunu bu iki hata için çürüttü. İddia, kod yazılmadan önce ölçüldüğü için
   ucuza düzeltildi.

   **Yine de `raise_for_status()` tek başına yetmez.** Üç sebeple:
   - Status ayrıntıyı söylemez: `403`, "key geçersiz" (10) ile "key askıya alındı"
     (26) arasını ayırt edemez. Teşhis gövdededir.
   - Retry kararı `error` koduna dayanır (kalıcı / geçici / rate limit ayrımı).
   - `raise_for_status()` fırladığı anda **gövde okunmadan akış kopar** — teşhis
     bilgisi kaybolur. Doğru sıra: önce gövdeyi oku, sonra hata fırlat.

   Bu, P2.1'in doğrudan gereksinimidir.

### İşe yarar metodlar

- **`chart.getTopTracks` — global en popüler parçalar. İlk dilimin metodu (1.4'te seçildi).**
- `chart.getTopArtists` · `artist.getTopTracks` · `geo.getTopArtists` · `tag.getTopTracks`

**Neden `chart.getTopTracks`:** `getTopArtists` düz bir tablo döndürür — transform katmanı
`DataFrame(data)` çağrısına indirgenir ve öğrenilecek bir şey kalmaz. `getTopTracks` iç içe
bir `artist` nesnesi, `duration` gibi sayısal bir alan ve aynı isimli alanın metoda göre
farklı tip alması gibi gerçek dönüşüm problemleri taşır. Seçim satır sayısı için değil,
**şema derinliği** için yapıldı.

**Tarih parametresi yok.** `chart.getTopTracks` geçmişe dönük sorgu kabul etmiyor
(ADR-0006). Sonucu: **API'den backfill imkânsız**, geçmiş yalnızca ileriye doğru birikir.
CLI ve backfill döngüsünün iptal gerekçesi budur.

### Rate limit

**Saniyede ~5 istek** (IP başına, 5 dakikalık ortalama üzerinden). Kaynak: Last.fm API
kullanım şartları, not 17'de kayıtlı.

> **Düzeltme:** bu dosyanın önceki hâli "dakikada ~5 istek" diyordu — yanlış, ve
> `PROGRESS.md`'nin 1.8 kaydıyla çelişiyordu. Aradaki fark 60 kat; bir throttle
> tasarımını tamamen değiştirecek büyüklükte.

Ayrıca ölçüldü (1.8): yanıtta `RateLimit-*` header'ı **yok**. Yani kalan kotayı
sunucudan öğrenme imkânı yok — throttle istemci tarafında kendi sayacını tutmalı.

---

## 4. Hedef mimari

Kursun mimarisi, Last.fm'e uyarlanmış. ADR-0010 bunu bağlayıcı kapsam olarak kabul eder.

```
Last.fm API
    │
    ▼
EventBridge (günlük)  ──►  Lambda: extract  ──►  S3 bucket 1 (raw)
                                                  raw/to_processed/*.json
                                                       │
                                                  (PUT event)
                                                       ▼
                                              Lambda: transform
                                                       │
                                    ┌──────────────────┴─────────────┐
                                    ▼                                ▼
                        S3 bucket 2 (transformed)          raw/processed/ (arşiv)
                        tracks/*.parquet
                        artists/*.parquet
                                    │
                                    ▼
                            Glue Crawler
                                    │
                                    ▼
                       Glue Data Catalog  (lastfm_db)
                                    │
                                    ▼
                              Athena (SQL)
```

**İki bucket, kursta olduğu gibi:**

| Bucket | İçerik |
|---|---|
| `...-lastfm-raw-<sen>` | `raw/to_processed/` → yeni dosyalar · `raw/processed/` → işlenmiş arşiv |
| `...-lastfm-transformed-<sen>` | `tracks/` · `artists/` (Parquet) |

Ayrı bucket olmasının sebebi sadece kursu takip etmek değil: transform Lambda'sının
çıktısı kendisini tetikleyen bucket'a yazılırsa **sonsuz döngü** olur. İki bucket bunu
yapısal olarak imkânsız kılar.

`raw/to_processed/` → `raw/processed/` taşıması kursun **idempotency mekanizmasıdır**:
işlenmiş dosya bir daha işlenmez ve neyin işlendiği görülebilir. P3.2'de bilinçli
kurulacak, kopyalanmayacak.

**Diyagrama dair iki not:**

- Kurs "CloudWatch (daily trigger)" diyor. Bu servisin güncel adı **EventBridge**.
  Aynı şey, isim değişti.
- Glue Crawler'ın **koşu başına maliyeti var** (~$0.44). Sabit bir şema için gereksiz;
  alternatifi tabloyu bir kez elle tanımlamak. Kursta olduğu için kullanılıyor,
  maliyeti P4.1'de ölçülüyor. Gerekçe: ADR-0010.

**Geliştirme verisi:** `tests/fixtures/lastfm/` altındaki kayıtlı payload'lar (ADR-0004).
Transform yazılırken her denemede S3'e gidilmez — fixture'la iterasyon, S3'e gerçek koşu.

---

---

## 5. Yol haritası

Proje **dört adımdan** (P1–P4, kursun dört parçası), toplam **14 alt adımdan** oluşur.
Alt adımlar, "bitti" tanımları ve öğrenilecek structure dersleri → [`ROADMAP.md`](ROADMAP.md)

Burada tekrarlanmaz. Plan revize edilirken iki dosyayı senkron tutmak, er ya da geç
tutmamak demektir.

---

## 6. "Bitti" ne demek — her adım için kontrol listesi

Bu **genel** listedir, her adım için geçerlidir. Adıma özel ek şartlar
[`ROADMAP.md`](ROADMAP.md)'de her adımın altında yazar.

- [ ] Kod çalışıyor ve ben **elimle** çalıştırıp doğruladım
- [ ] İki kere çalıştırdığımda aynı sonucu veriyor (idempotent)
- [ ] Hata durumunda **sessizce başarılı olmuyor** — gürültülü şekilde patlıyor
- [ ] Log satırları bir sorunu teşhis etmeye yetiyor
- [ ] Sırf "ileride lazım olur" diye yazılmış kod yok
- [ ] Anlamlı bir commit mesajıyla commit edildi
- [ ] `docs/PROGRESS.md` güncellendi
- [ ] Geri alması pahalı bir karar içeriyorsa `docs/adr/` altına ADR yazıldı
- [ ] Not yazıldıysa **koddan sonra** yazıldı

---

## 7. Öğrenmek istediğim kavramlar

Bu terimler geçtiğinde üstünden hızla geçme — durup açıkla:

**Temel:** idempotency · immutable raw layer · data grain · partitioning ·
watermark / incremental load · schema-on-read vs schema-on-write

**Kalite:** data contract · şema doğrulama · null/uniqueness/row-count kontrolleri ·
fail-fast vs fail-safe · dead letter queue

**Operasyon:** exponential backoff · structured logging · observability · alerting ·
least privilege · at-least-once delivery

**Mimari:** medallion (bronze/silver/gold) · ELT vs ETL · batch vs streaming ·
maliyet optimizasyonu (dosya boyutu, partition sayısı, taranan byte)

---

## 8. Dokümantasyon yapısı

| Yol | Ne tutar | Dil | Ne sıklıkla değişir |
|---|---|---|---|
| `docs/PROJECT_CONTEXT.md` | Sabit sözleşme — hedef, tercihler, mimari, çalışma anlaşması | TR | Nadiren |
| `docs/ROADMAP.md` | **Plan.** Alt adımlar, bitti tanımları, bağımlılıklar | TR | Adım revize edildikçe |
| `docs/PROGRESS.md` | **Güncel durum.** Tek durum kaynağı | TR | Her alt adımda |
| `docs/adr/` | Bu projeye özel, geri alması pahalı kararlar | EN | Karar çıktıkça |
| `docs/notes/` | Genel öğrenme notları — **ne** ve **neden** | TR | Adım **bittikten sonra** |
| `docs/runbooks/` | **Prosedür** — bir işi baştan tekrar etme tarifi | TR | İş yapıldıkça |
| `docs/annotated/` | `src/` altındaki her `.py`'nin satır satır yorumlu aynası | TR | Her yeni `.py` ile aynı commit'te |
| `docs/TOOLING.md` | Araç manzarası — başvuru haritası | TR | Nadiren. Bu turda araç seçilmiyor |

`adr/` mi `notes/` mi? Testi: *"Bu bilgi başka bir projede de geçerli mi?"*
Evetse `notes/`, hayırsa `adr/`.

`notes/` mi `runbooks/` mi? Testi: *"Bu bir bilgi mi, bir eylem dizisi mi?"*
Bilgiyse `notes/` (okunur), eylem dizisiyse `runbooks/` (uygulanır). "Credential chain
nedir" → `notes/`; "AWS hesabını sıfırdan nasıl kurarım" → `runbooks/`.

**Runbook kuralı:** bir konsol/terminal prosedürü **yapıldığı oturumda** runbook'a yazılır.
Sebep ölçüldü (2026-08-22): P1.2'nin tamamı — hesap, MFA, budget, IAM kullanıcı, access key —
yapıldı ama hiçbir yerde tekrar edilebilir biçimde durmuyordu. Kavram notu bu boşluğu
doldurmaz; not "credential chain nedir"i anlatır, "bunu nasıl kurmuştum"u değil.

`notes/` mi `TOOLING.md` mi? Testi: *"Bu bilgi bir alt adıma bağlı mı?"*
Bağlıysa `notes/` — o anın öğrenmesidir, dondurulur. Bağlı değilse ve **araç seçerken**
açılacaksa `TOOLING.md`.

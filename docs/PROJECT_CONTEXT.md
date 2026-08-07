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
gerçekten çalışan bir pipeline istiyorum. Ama asıl kazanım kodun kendisi değil, kod yazarken
öğrendiğim karar verme biçimi.

**Öğrenme tarzım:** Adım adım, açıklaya açıklaya. Kodu ben yazmak istiyorum — Claude'un
benim yerime `src/` altına dosya oluşturmasını istemiyorum.

**Kapsam:** Tek tek dosyaların içeriğini değil, **projenin en tepesinden en dibine kadar**
her kararı öğrenmek istiyorum. Klasör yapısının neden böyle olduğundan, bir değişkenin neden
o isimle çağrıldığına kadar. Git akışı, isimlendirme kuralları, tooling seçimi, bağımlılık
yönetimi — bunlar "konu dışı temel şeyler" değil, konunun kendisi.

### Geçmiş deneyim — tekrarlamak istemediğim hatalar

**Not: Aşağıdaki proje terk edildi. Kodu kullanılmayacak, sadece ders listesi.**

Bir Spotify ETL projesine başlamıştım. Spotify API'de aradığım veriye ulaşamayınca
(audio features endpoint'i kısıtlandı, playlist verisi yetersiz kaldı) Last.fm'e geçmeye
karar verdim. O denemeden çıkardıklarım:

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

## 2. Teknik tercihler

| Konu | Karar |
|---|---|
| Sohbet dili | Türkçe |
| Kod / docstring / commit / README / ADR dili | İngilizce |
| `docs/notes/` dili | Türkçe (öğrenme defteri) |
| Python | 3.12+ |
| Paket yönetimi | `uv` veya `pip` + `pyproject.toml` |
| Kapsam | Önce tamamen local çalıştır, sonra aynı kodu AWS'ye taşı |
| Bulut | AWS (S3, Lambda, EventBridge, Glue, Athena) |
| Depo formatı | Raw: JSON — Transformed: Parquet |

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
| Hata davranışı | HTTP status kodu doğru | **Hatada bile HTTP 200** dönebilir |

### İki kritik tuzak

1. **`format=json` unutulursa** → XML döner, `response.json()` patlar.
2. **Hata gövdenin içinde gelir** → HTTP 200 ile birlikte
   `{"error": 10, "message": "Invalid API key"}`. Yani `raise_for_status()` yetmez,
   gövdede `error` anahtarı var mı diye ayrıca bakmak gerekir.
   Bu, "sessiz başarı" hatasının ders kitabı örneği.

### İşe yarar metodlar

- `chart.getTopArtists` — global en popüler sanatçılar
- `chart.getTopTracks` — global en popüler parçalar
- `artist.getTopTracks` — bir sanatçının en popüler parçaları
- `geo.getTopArtists` — ülke bazlı (`country=turkey`)
- `tag.getTopTracks` — tür/etiket bazlı

### Rate limit

Resmî olarak dakikada ~5 istek (IP başına). Yani retry ve backoff süs değil, zorunluluk.

---

## 4. Hedef mimari

```
Last.fm API
    │
    ▼
[EXTRACT]  api client → ham JSON, hiç dokunulmadan
    │
    ▼
raw/ ── s3://bucket/raw/lastfm/method=chart_gettopartists/dt=2026-08-07/data.json
    │      (immutable — bir kez yazılır, asla değiştirilmez)
    ▼
[TRANSFORM]  şema doğrulama → düzleştirme → tip dönüşümü
    │
    ▼
curated/ ── s3://bucket/curated/top_artists/dt=2026-08-07/part-0.parquet
    │
    ▼
[LOAD]  Glue Crawler → Data Catalog → Athena ile SQL
```

**Tetikleyici:** Local'de manuel / cron → AWS'de EventBridge (günlük)

Local'de veri gölü `/data/raw/` ve `/data/curated/` altında yaşar — S3 yapısını birebir
taklit eder, böylece AWS'ye taşırken yol mantığı değişmez. `/data/` gitignore'ludur.

---

## 5. Yol haritası

Proje 9 adımdan oluşur. Adımların alt adımları, "bitti" tanımları, ADR adayları ve
aralarındaki bağımlılıklar → [`ROADMAP.md`](ROADMAP.md)

Burada tekrarlanmaz. Plan revize edilirken iki dosyayı senkron tutmak, er ya da geç
tutmamak demektir.

Her adım bitince commit atılır. Bir sonrakine geçmeden önce çalıştığı doğrulanır.

---

## 6. "Bitti" ne demek — her adım için kontrol listesi

Bu **genel** listedir, her adım için geçerlidir. Adıma özel ek şartlar
[`ROADMAP.md`](ROADMAP.md)'de her adımın altında yazar.

Bir adım şu şartları sağlamadan bitmiş sayılmaz:

- [ ] Kod çalışıyor ve ben **elimle** çalıştırıp doğruladım
- [ ] İki kere çalıştırdığımda aynı sonucu veriyor (idempotent)
- [ ] Hata durumunda **sessizce başarılı olmuyor** — gürültülü şekilde patlıyor
- [ ] Log satırları bir sorunu teşhis etmeye yetiyor
- [ ] Sırf "ileride lazım olur" diye yazılmış kod yok
- [ ] Anlamlı bir commit mesajıyla commit edildi
- [ ] `docs/PROGRESS.md` güncellendi
- [ ] Tasarım kararı içeriyorsa `docs/adr/` altına ADR yazıldı
- [ ] Yeni öğrenilen genel bilgi `docs/notes/` altına yazıldı

---

## 7. Öğrenmek istediğim kavramlar

Bu terimler geçtiğinde üstünden hızla geçme — durup açıkla:

**Temel:** idempotency · immutable raw layer · data grain · partitioning ·
backfill · watermark / incremental load · schema-on-read vs schema-on-write

**Kalite:** data contract · şema doğrulama · null/uniqueness/row-count kontrolleri ·
fail-fast vs fail-safe · dead letter queue

**Operasyon:** exponential backoff · circuit breaker · structured logging ·
observability (log/metric/trace) · alerting · SLA

**Mimari:** medallion (bronze/silver/gold) · ELT vs ETL · batch vs streaming ·
orchestration DAG'ı · maliyet optimizasyonu (dosya boyutu, partition sayısı)

---

## 8. Dokümantasyon yapısı

| Yol | Ne tutar | Dil | Ne sıklıkla değişir |
|---|---|---|---|
| `docs/PROJECT_CONTEXT.md` | Sabit sözleşme — hedef, tercihler, mimari | TR | Nadiren |
| `docs/ROADMAP.md` | **Plan.** Alt adımlar, bitti tanımları, bağımlılıklar | TR | Adım revize edildikçe |
| `docs/PROGRESS.md` | **Güncel durum.** Tek durum kaynağı. | TR | Her alt adımda |
| `docs/adr/` | Bu projeye özel mimari kararlar | EN | Karar çıktıkça |
| `docs/notes/` | Genel öğrenme notları | TR | Konu öğrenildikçe |

`adr/` mi `notes/` mi? Testi: *"Bu bilgi başka bir projede de geçerli mi?"*
Evetse `notes/`, hayırsa `adr/`.

# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-15
**Current step:** A — Extract + raw load (dlt) ([plan](ROADMAP.md#adım-a--extract--raw-load-dlt))
**Next sub-step:** A.1 — dlt'nin modeli: source / resource / destination / pipeline / state

> **ADIM 0 TAMAMLANDI.** **ADIM 1 TAMAMLANDI** (1.1–1.8).

### Sıradaki oturumda ilk iş

Bu blok, iki makine arasında geçiş yaparken tek bakılacak yerdir.

1. `git pull`
2. Bu dosyayı ve `ROADMAP.md`'nin **Adım A** bölümünü oku. Plan tamamen değişti
   (aşağıdaki revizyon bölümü) — eski 2/3/4/5 adımlarını arama, yoklar.
3. Karar bekleyen tek şey: **önce `PROJECT_CONTEXT.md` düzeltmesi mi, doğrudan A.1 mi?**
   (İkisi de yapılacak, sadece sıra seçilmedi.)

**Açık işler:**

| # | İş | Durum |
|---|---|---|
| 1 | `PROJECT_CONTEXT.md` §2 ve §4: ETL → ELT, mimari şemasına dlt/dbt/DuckDB | Yapılmadı. ADR-0008 bunu geçersiz kıldı. |
| 2 | Repo adı `LastFM-ETL-...` → ELT | Yapılmadı. GitHub'da elle. |
| 3 | 1.8 teyidi (opsiyonel, 2 dk) | `chart.getTopTracks`'e `&date=2020-01-01` ekleyip çıktı değişiyor mu bak. ADR-0006 "tarih parametresi yok" diyor ama bunun ölçüm mü okuma mı olduğu belirsiz. Sonuç C adımındaki backfill iptalinin dayanağı. |
| 4 | ADR-0006'nın üç şartını dlt paginator'ına karşı doğrula | A.3'te yapılacak. Özellikle: "hedef sayıya ulaşmadan sayfalar biterse **hata**" — dlt bunu ifade edemiyorsa boşluk notlanacak. |
| 5 | `PROGRESS.md`'nin "Tamamlananlar" geçmişi | Budanmadı, karar Barış'ta. |

**Kurulu olmayanlar:** `dlt` ve `dbt-duckdb` henüz bağımlılık olarak eklenmedi.
A.1 bir okuma/anlama adımı — kurulum A.2'de.

---

## ROADMAP REVİZYONU — 2026-08-15

Plan araç-merkezli tek tura çevrildi. 9 adım → 5 adım (A–E).

| | Önce | Sonra |
|---|---|---|
| Extract + raw | Elle `requests` client, retry, backoff, sayfalama, atomic write (adım 2, 3, 4) | **dlt** — `rest_api` source + `filesystem` destination (adım A) |
| Transform | Pydantic + pandas (adım 5) | **dbt-duckdb** — staging + mart + veri testleri (adım B) |
| Mimari | ETL | **ELT** |
| İptal | — | CLI/backfill, mypy strict, pre-commit, Docker, Glue Crawler |

Gerekçeler: ADR-0007 (dlt), ADR-0008 (dbt + ELT). Eski numaraların nereye gittiği
`ROADMAP.md`'deki eşleme tablosunda — eski numaralar **yeniden kullanılmadı**.

**Bu revizyonun bedeli, açıkça:** elle HTTP client, retry ve atomic write yazma
pratiği feda edildi. Karşılığı Adım 1'in ölçümleri + A.3/A.6'da dlt'nin davranışını
inceleme. Takas bilinçli, bedava değil.

**Notlar ve ADR'ler kısılmadı.** Her adımda tam yazılıyor. Değişen tek şey:
uygulamadan önce yazılan notlar kaynak etiketi taşıyacak —
`> Kaynak: ÖLÇÜLDÜ (tarih)` veya `> Kaynak: OKUNDU — henüz uygulanmadı`.
Gerekçe: `PROJECT_CONTEXT.md` bir süre "hatada HTTP 200 döner" diyordu; okunmuş
bilgi notta ölçülmüş gibi durursa aynı hata tekrarlanır.

**Adım 1 kapanışı — 1.8:** rate limit ölçümü tamamlandı (header yok, belgelenen limit
5 istek/sn, `limit` parametresinin davranışı ölçüldü, aktif sondaj bilinçli olarak
yapılmadı). Tarih parametresi sorusu ADR-0006'da zaten kapalı: `chart.getTopTracks`
tarih parametresi kabul etmiyor → **API'den backfill imkânsız**, geçmiş yalnızca
ileriye doğru birikir. Bu, C adımındaki CLI/backfill iptalinin de gerekçesi.

**Bekleyen düzeltme:** `PROJECT_CONTEXT.md` ve repo adı hâlâ "ETL" diyor. ADR-0008
bunu geçersiz kıldı. A.1'den önce düzeltilecek.

---

## Tamamlananlar

- [x] **0.1** `.gitignore` yazıldı ve `git check-ignore -v` ile doğrulandı.
      Kritik kontrol: `src/lastfm_etl/raw` **eşleşmedi** — kalıplar yeterince dar yazılmış.
- [x] **0.2** İlk commit atıldı: `chore: add .gitignore`
- [x] `docs/` yapısı kuruldu (PROGRESS, ADR, notes) — `docs: add project documentation structure`
      ADR-0001 yazıldı, `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı,
      custom instructions yenilendi.
- [x] **CRLF/LF normalizasyonu** (ROADMAP'te yazmayan, araya giren iş).
      `.gitattributes` ile `* text=auto eol=lf` — `chore: enforce LF line endings via .gitattributes`
      Semptom: içerik değişmeden `1127 insertions / 1127 deletions`. Sebep: iş
      makinesi tüm docs'u CRLF ile yeniden yazmıştı.
      `git ls-files --eol` ile `i/lf w/lf` doğrulandı. Not: `docs/notes/03-line-endings.md`
- [x] **0.3** `pyproject.toml` + `src/` layout.
      Paket adı kararı: dağıtım `lastfm-etl`, import `lastfm_etl`. Önceki
      `src/lastfm-pipeline/` klasörü silindi — tire içeren isim `SyntaxError` verir,
      import edilemez. Boş alt klasörler (`extract/`, `transform/`, `load/`, `utils/`)
      açılmadı: modül yapısı Adım 1'de gerçek payload görüldükten sonra kararlaşacak.
      ADR-0002 yazıldı. Notlar: 04, 05, 06.
      **Uyarı:** kurulabilirlik doğrulanmadı — venv 0.4'te geliyor.
- [x] **`.gitignore` düzeltmesi** (ROADMAP'te yazmayan, araya giren iş).
      `.gitignore` **satır sonu yorumu desteklemez** — sadece `#` ile *başlayan* satır
      yorumdur. `__pycache__/`, `*.py[cod]`, `*.egg-info/` ve `.venv/` pattern'ları
      yorum metnini de içerdiği için **hiçbir şeyle eşleşmiyordu**.
      `fix: correct .gitignore patterns broken by inline comments`
      0.1'deki doğrulama `.env` ve `data/` üzerinden yapıldığı için (o satırlarda inline
      yorum yok) fark edilmemişti. Ders: doğrulama **örnek** üzerinden değil, **her
      pattern** üzerinden yapılır. Not: `docs/notes/01`.
- [x] **0.4 kararı:** `uv`, project mode. ADR-0003 yazıldı.
      Gerekçe özeti: 8.6 zaten lock dosyası istiyor; `uv` onu, dev/prod ayrımını ve
      Python sürüm yönetimini tek araçta veriyor. "Önce venv+pip, sonra uv" alternatifi
      reddedildi — üç araç öğrenmek demek olurdu ve `uv` zaten `.venv/`/`pyvenv.cfg`/
      `PATH` mekanizmasını gizlemiyor. Notlar: 07, 08.
- [x] **0.4** Sanal ortam kuruldu. `uv` 0.12.2 (winget), `uv sync` → `.venv/` + `uv.lock`.
      **PROGRESS ile ADR-0003 çelişkisi düzeltildi:** buradaki eski sıra
      `uv venv` → `uv pip install -e .` idi; bu **pip mode**'dur ve `uv.lock`'a bakmaz,
      yani ADR'de reddedilen modelin komutlarıydı. Project mode'da doğru komut tek:
      `uv sync`. Not: 09.
      **0.3'ün devredilmiş doğrulaması geçti** —
      `uv run python -c "import lastfm_etl; print(lastfm_etl.__file__)"` çıktısı
      `src\lastfm_etl\__init__.py`, `site-packages` altı değil. Editable install çalışıyor,
      0.3 artık gerçekten kapalı.
      `git status` temiz kaldı: `.venv/` ignore'lu, sadece `uv.lock` yeni dosya olarak çıktı.
- [x] **0.5** `.env.example` + `README.md`.
      `.env.example` şimdilik tek anahtar (`LASTFM_API_KEY`, değeri boş). `LASTFM_USER`
      gibi adaylar bilinçli olarak eklenmedi — config mi CLI argümanı mı olacağı 2.1'in
      konusu. **Devredilen doğrulama:** `.env.example` ile gerçek `.env` arasındaki
      anahtar senkronu 1.1'de (gerçek key alınınca) doğrulanacak.
      README altı bölüm: özet, status, prerequisites, setup, structure, docs haritası.
      Usage/badge/mimari şeması bilinçli olarak **yok** — çalışan komut yokken yazmak
      "aspirational README" olurdu. 8.8'de eklenecek. Not: 10.
- [x] **`check-ignore` tuzağı** (araya giren iş). `git check-ignore -v .env.example`
      exit `0` döndürdü ve dosya ignore'luymuş gibi göründü — oysa değildi.
      Sebep: `-v` bayrağı exit code'un anlamını değiştiriyor ("ignore'lu" değil,
      "bir pattern ile eşleşti" — negation dahil). Doğrulama `git status` /
      `git add --dry-run` ile yapılır. Not 01'e Tuzak 3 olarak eklendi.
- [x] **0.6 — ADIM 0 KAPANDI.** Bitti tanımının beş maddesi:

      | Madde | Nasıl doğrulandı |
      |---|---|
      | `git status` temiz, türev dosya yok | `.venv/`, `*.egg-info/`, `uv.lock` sonrası temiz |
      | `.env` ve `data/` gerçekten ignore'lu | `git check-ignore` + `git status` (boş `.env` ile) |
      | Paket temiz ortamda kurulup import edilebiliyor | `uv run python -c "import lastfm_etl"` → `src/` yolu |
      | `.env.example` var, gerçek `.env` yok | Doğrulandı; **anahtar senkronu 1.1'e devredildi** |
      | README bir yabancıya yetiyor | Boş klasörde `git clone` + README'yi sıfırdan takip — geçti |

- [x] **İş makinesi ortamı kuruldu** (ROADMAP'te yazmayan, araya giren iş).
      `winget install --id=astral-sh.uv -e` → terminal kapat-aç → `uv sync`.
      Doğrulama geçti: `import lastfm_etl` çıktısı `src\lastfm_etl\__init__.py`,
      `git status` temiz. İki makine artık aynı `uv.lock`'tan besleniyor.
- [x] **1.1** Last.fm API key alındı, `.env`'e yazıldı.
      **Shared Secret bilinçli olarak eklenmedi.** Gerekçe: bu proje yalnızca public
      chart metodlarını (`chart.getTopArtists` vb.) çağırıyor; bunlar sadece `api_key`
      ister. `shared_secret` yalnızca `api_sig` üretmek için gerekir — yani authenticated
      metodlarda (`track.scrobble`, kullanıcıya özel veri). Kullanılmayan bir sır sıfır
      fayda sağlar ama sızma yüzeyini büyütür; ayrıca `.env.example`'a eklenirse sözleşme
      yalan söyler.
      Ayrım: `api_key` **kim olduğunu** söyler, `shared_secret` **o olduğunu kanıtlar**.
      **0.5'ten devredilen doğrulama kapandı:** `git status` gerçek sır içeren `.env`'i
      göstermiyor, `git status --ignored --short` `!! .env` diyor, `.env.example` ile
      anahtar seti birebir aynı (tek anahtar: `LASTFM_API_KEY`).
- [x] **1.2** API elle çağrıldı (`curl.exe`), `format=json` ile ve olmadan.
      **Ölçüm — tuzak gözle doğrulandı:**

      | | `format` yok | `format=json` |
      |---|---|---|
      | Status | `200` | `200` |
      | `Content-Type` | `text/xml` | `application/json` |
      | Gövde ilk karakteri | `<` | `{` |

      Kritik sonuç: **iki cevabın status kodu aynı.** `raise_for_status()` bu durumu
      yakalayamaz; ayrım yalnızca `Content-Type` header'ında ve gövdede görünür.
      Sır komut geçmişine sokulmadı — `.env` önce oturuma yüklendi, URL'de
      `$env:LASTFM_API_KEY` kullanıldı. Metod seçimi keyfi değil: `PROJECT_CONTEXT.md` §4
      zaten `method=chart_gettopartists` yolunu varsayıyor.
      Not: `docs/notes/11`.

- [x] **1.3** Bozuk `api_key` ile çağrıldı. **Ölçüm, beklentiyi çürüttü.**

      | Deney | Status | Content-Type | Gövde |
      |---|---|---|---|
      | Bozuk `api_key` | `403` | `application/json` | `{"message":"Invalid API key...","error":10}` |
      | Bozuk `method` | `400` | `application/json` | `{"message":"Invalid Method...","error":3}` |

      Beklenti `200` + gövdede hata idi (`PROJECT_CONTEXT.md` §3'ün eski hâli ve
      Claude'un iddiası). Gerçek: Last.fm HTTP status kodlarını **doğru** kullanıyor.
      `Content-Type: application/json` ve gövde formatı, cevabın araya giren bir
      WAF/CDN'den değil Last.fm'in kendisinden geldiğini kanıtlıyor.
      `PROJECT_CONTEXT.md` §3 ölçüme göre düzeltildi.
      **Ders:** iddia, kod yazılmadan önce ölçüldüğü için ucuza düzeltildi. Adım 1'in
      var oluş sebebi tam olarak bu.
      **Gövde kontrolü yine de zorunlu, ama gerekçesi değişti** — "HTTP yalan söylüyor"
      değil, "HTTP yeterince şey söylemiyor": `403` tek başına `error 10` (geçersiz key)
      ile `error 26` (askıya alınmış key) arasını ayırt edemez, retry sınıfını belirleyemez,
      ve `raise_for_status()` fırladığı anda gövde okunmadan akış kopar.
      **Yan bulgu:** `requests`, `HTTPError` mesajına **tam URL'yi** gömüyor — query
      string dahil. Gerçek key kullanılsaydı traceback'te düz metin olarak dururdu.
      Not 11 §8.2'deki teorik risk canlı kanıtla doğrulandı. Maskeleme 3.7'de.
      **ADR adayı düzeltmesi:** ROADMAP'te 3.3 için yazan
      *"Treat HTTP 200 with an error body as a failure"* başlığı ölçüme uymuyor;
      ADR yazılırken *"Validate both HTTP status and response body"* olacak.

- [x] **METOD DEĞİŞİKLİĞİ (1.4'te alındı):** ilk dilim `chart.getTopArtists` yerine
      **`chart.getTopTracks`** ile yapılacak. Gerekçe satır sayısı **değil** (o `limit`
      parametresine bağlı), **şema derinliği**: `getTopTracks` iç içe `artist` nesnesi,
      `duration` gibi sayısal alan ve `streamable`'ın metoda göre farklı tip alması gibi
      gerçek dönüşüm problemleri taşıyor. `getTopArtists` düz bir tablo — transform katmanı
      tek satıra inerdi ve 5.4 (düzleştirme) öğrenilmeden geçilirdi.
      `PROJECT_CONTEXT.md` §3 ve §4 buna göre güncellendi.
- [x] **1.4** Üç payload `tests/fixtures/lastfm/` altına kaydedildi:
      `chart_gettoptracks_success.json` (31 KB, 20 parça), `error_10_invalid_api_key.json`,
      `error_3_invalid_method.json`. ADR-0004 yazıldı.
      **Konum kararı:** `docs/samples/` değil `tests/fixtures/`. Gerekçe: *doğrulanan
      kaynak kazanır* — test kodu dosyayı gerçekten okur, yol değişirse test kırılır.
      Dokümanı çalıştıran bir şey yok, orada dosya silinse kimse fark etmez. Doküman
      payload'ı **kopyalamaz, link verir**; iki kopya kaçınılmaz olarak sapar.
      **Biçim kararı:** pretty-printed (`json.tool --no-ensure-ascii`). Ana gerekçe
      okunabilirlik değil **git diff**: tek satırlık JSON'da alan değişikliği görünmez.
      `--no-ensure-ascii` olmadan non-ASCII karakterler `\uXXXX` kaçışlarına dönüşürdü.
      **Bu kural raw katmanın tam tersi** (4. adım byte düzeyinde sadakat istiyor) —
      aynı veri, farklı amaç, farklı kural. Karıştırılırsa 4.1'in tuzağına düşülür.
      **Güvenlik kontrolü geçti:** `grep -rn "api_key" tests/` → eşleşme yok. Payload
      isteği yankılamıyor. Her yeni fixture'da tekrarlanmalı.
- [x] **Shell bilgisi boşluğu kapatıldı** (araya giren iş). `\`, `|`, `>`, `&&`, `||`,
      `/dev/null`, exit code, `export`/`source`/`set -a` ve kullanılan komutlar
      (`ls`, `mkdir -p`, `grep`, `echo`) not 12'de toplandı. Ayrıca bash ↔ PowerShell
      sözlüğü. Gerekçe: `PROJECT_CONTEXT.md` §7 shell'i "konunun kendisi" sayıyor;
      CI, Dockerfile, cron ve Makefile hep shell.
      **Düzeltme:** verdiğim komutlardaki `set -a` teknik olarak gereksizdi — `$VAR`
      komut satırında geçtiğinde bash onu zaten genişletiyor. Export yalnızca alt süreç
      (`os.environ`) okuyacaksa gerekli. Adım 2'de gerekli olacağı için alışkanlık
      olarak yazıldı.

- [x] **1.5** Payload anatomisi ölçüldü. Not 13 (keşif protokolü) yazıldı.

      **Yapı:** `{"tracks": {"track": [...], "@attr": {...}}}`. Bir kaydın alanları:
      `name, duration, playcount, listeners, mbid, url, streamable, artist, image`.
      `artist` ve `streamable` iç içe nesne, `image` dört elemanlı dizi.

      **XML kökeni her şeyi açıklıyor.** Last.fm JSON üretmiyor — XML üretip çeviriyor.
      Üç sonucu var: (1) **istisnasız her sayı string** (`"duration": "184"`, `@attr`
      içindeki sayfa numaraları dahil), çünkü XML'de tip yok; (2) `#text` anahtarı bir
      veri değil **yapı kalıntısı** — XML'de `<image size="small">url</image>` gibi hem
      öznitelik hem metin taşıyan eleman JSON'a böyle çevrilir; (3) XML'de `null`
      kavramı olmadığı için eksik veri `""` olarak gelir, `None` olarak değil.
      Ölçüldü: payload'da hiç `None` yok.

      **Tek elemanlı liste tuzağı YOK.** `limit=1` ile ölçüldü → `list` döndü, tek dict
      değil. Yani 5. adımda normalizasyon kodu (`if isinstance(t, dict): t = [t]`)
      **yazılmayacak**. Ölçmeseydik "her ihtimale karşı" yazılırdı — §6'nın yasakladığı
      şey. Ölçüm bazen kod eklettirir, bazen kod yazdırmaz.

      **EN ÖNEMLİ BULGU — ilk sayfa yalan söyledi.** Aynı endpoint, aynı gün, tek fark
      `page` numarası:

      | Ölçüm | `page=1` | `page=500` |
      |---|---|---|
      | Kayıt sayısı | 20 | **19** |
      | Boş `mbid` (track) | 0 | **4 (%21)** |
      | Boş `mbid` (artist) | 0 | 1 |
      | `duration == 0` | 0 | **2** |
      | Alan setleri aynı mı | True | **False** |

      Sebep: chart popülerlik sıralı. En popüler kayıtlar en iyi kürate edilmiş olanlar —
      ilk sayfa veri kalitesinin **en yüksek** olduğu yer. Adı: **seçim yanlılığı**.

      **`mbid` bazen boş değil, anahtar olarak HİÇ YOK.** Kuyruktaki örnek kayıtta
      `mbid` anahtarı dict'te bulunmuyor. Yani üç ayrı durum var: `x["mbid"]` → `KeyError`,
      `x.get("mbid")` → `None`, `x.get("mbid","")` → `""`. İlk sayfayla test eden kod
      kuyrukta patlar.

      **`image` dolu görünen boş alan.** 20 parça × 4 boyut = 80 URL beklenirken
      **4 benzersiz URL** çıktı — hepsi Last.fm'in "resim yok" varsayılanı
      (`2a96cbd8b46e442fc41c2b86b821562f.png`). Null kontrolünden geçer, içeriği çöp.
      `isna()` tipi kontroller bunu **yakalamaz**.

      **`duration == 0` belirsiz.** Parça 0 saniye mi, süre bilinmiyor mu? API ayırt
      etmiyor. Ortalama süre hesabında 0'lar sonucu bozar. `0 → null` çevrilmeli mi,
      5.4'ün kararı.

      **`@attr` sayfalama bilgisi:** `page, perPage, totalPages, total` — hepsi string.
      `total: 10000` ve `totalPages: 500` tam çarpım (500×20) veriyor, yani gerçek sayım
      değil **tavan** olma ihtimali yüksek. Son sayfanın 19 kayıt döndürmesi `total`'ın
      zaten tutarsız olduğunu gösteriyor.

      **İkinci fixture eklendi:** `chart_gettoptracks_edge_cases.json` (page=500).
      Gerekçe: mevcut fixture'da hiç edge case yoktu, 7.4'ün testleri onunla yazılamazdı.
      Dosya adı `page500` değil `edge_cases` — ad, verinin **nereden geldiğini** değil
      **ne işe yaradığını** söylemeli.

- [x] **1.6** Grain karara bağlandı. ADR-0005 yazıldı, not 14 eklendi.

      > **Bir satır = bir UTC gününde, Last.fm global top-tracks chart'ında görünen bir
      > parçanın o çekim anındaki durumu.**

      Birincil anahtar: **`(snapshot_date, artist_name, track_name)`**
      Kimball terimiyle: **periodic snapshot fact table**.

      **Ölçüm — iki anahtar adayı da tam benzersiz çıktı:**

      | Dosya | rows | `name+artist` | `url` | tekil `artist` |
      |---|---|---|---|---|
      | `..._success.json` (page=1) | 20 | 20 | 20 | **6** |
      | `..._edge_cases.json` (page=500) | 19 | 19 | 19 | 19 |

      `url` fazladan ayrım yapmıyor — aynı iki alanın URL-encode edilmiş hali.
      Seçim `(artist_name, track_name)`; `url` normal kolon olarak saklanıyor.
      Gerekçe: URL bir **kimlik değil adres**tir — anahtar yapmak veri modelini Last.fm'in
      site yapısına bağlar ve her filtreyi encode'lu string karşılaştırmasına çevirir.
      Kabul edilen bedel: isim değişirse geçmiş satırlar eski adı taşır (snapshot
      semantiğinin doğal sonucu, bug değil — veri kaybolmuyor, isim üzerinden uzun aralıklı
      join garanti edilemiyor).

      **`mbid` anahtara girmedi.** Öznitelik olarak kalıyor. Üç gerekçe: (1) kuyrukta
      4/19 kayıtta anahtar **yok**, NULL bileşenli `UNIQUE` SQL'de zorlanamaz
      (`NULL != NULL`); (2) MusicBrainz'in kimliği, Last.fm'in değil — yabancı sistemin
      anahtarı; (3) dün boş bugün dolu olabilir, anahtar değişirse aynı parça yeni kayıt
      gibi görünür. **Genel kural:** anahtara alan eklemek onu güçlendirmez, grain'i
      **inceltir** ve çiftlenme riskini artırır.

      **PROGRESS düzeltmesi — 1.5'teki ifade yanlıştı.** 1.5'te `mbid` için "%21 **boş**"
      yazılmıştı; ölçüm bunu çürüttü: `anahtar yok 4, boş string 0, dolu 15`. Yani boş
      değil, **eksik**. Kod farkı: `x.get("mbid")` → `None` riski var, `""` riski **yok**.
      5.4'te `if mbid == "":` dalı yazılmayacak. (Uyarı: `artist.mbid` ayrı ölçülmedi,
      1.5 orada "boş" demişti — 1.7'de kontrol edilecek.)

      **En kritik düzeltme — "üzerine yaz, son playcount kalsın" reddedildi.**
      İlk cevabım tek satır tutup güncellemekti. Bu SCD Type 1'dir ve burada bilgi
      imhasıdır: `playcount` **kümülatif sayaç**, günlük artış ancak iki snapshot farkından
      türetilir (`playcount(t) - playcount(t-1)`). Üzerine yazınca fark sonsuza kadar
      kaybolur. Ve `chart.getTopTracks` tarih parametresi almıyor — çekilmeyen gün
      **kalıcı boşluk**. Hata sessizdir: pipeline hiç patlamaz, aylar sonra "trend
      çıkaralım" denince verinin hiç var olmadığı anlaşılır.
      OLTP (bugünkü durumun aynası) ≠ OLAP (kaynağı zaman içinde gözlemlemek).

      **`snapshot_date` ≠ `ingested_at` — iki ayrı kolon kalıyor.** Normal koşuda
      çakışıyorlar; backfill'de ayrışıyorlar (`ingested_at` bugün, `snapshot_date` geçmiş).
      Tek kolon biri hakkında yalan söylemek zorunda kalır.

      **Gün UTC.** Tercih değil zorunluluk: ev (TRT) + iş + 9.7'de Lambda (UTC).
      `date.today()` local döner, aynı chart iki farklı `snapshot_date` alır ve anahtar
      ortamdan ortama değişir. `datetime.utcnow()` de yanlış — tz bilgisi taşımıyor.
      Doğrusu `datetime.now(timezone.utc)`.

      **Bedava gelen sonuç:** anahtara tarih girdiği için aynı günün tekrar koşusu aynı
      anahtarı üretir → `snapshot_date` partition overwrite ile satır sayısı artmaz.
      4.5, 5.7 ve 6.8 grain'den türedi, sonradan eklenmedi.

      **Artist boyut tablosu açılmadı.** Page 1'de 6 sanatçı 20 parçayı paylaşıyor, yani
      dimension savunulabilir — ama ROADMAP'te sanatçı özniteliği isteyen sorgu yok, ikinci
      tablo yazma yolunu ve idempotency yüzeyini ikiye katlar. Denormalize kalıyor.

- [x] **1.7** Hedef şema karara bağlandı. Not 15 yazıldı. 1.6'nın iki borcu kapandı.

      **Tablo:** `lastfm_chart_top_tracks_daily`
      **Grain:** bir satır = bir UTC gününde chart'ta görünen bir parçanın o andaki durumu
      **PK:** `(snapshot_date, artist_name, track_name)` — **Partition:** `snapshot_date`

      | # | kolon | kaynak yol | tip | null? | gerekçe |
      |---|---|---|---|---|---|
      | 1 | `snapshot_date` | *türetilmiş* `datetime.now(timezone.utc).date()` | `date` | hayır | Anahtar bileşeni + partition. ADR-0005. |
      | 2 | `rank` | *türetilmiş* `(page-1)*perPage + i + 1` | `int32` | hayır | Sıra hiçbir kolondan geri hesaplanamaz — ölçüldü. |
      | 3 | `artist_name` | `track.artist.name` | `string` | hayır | Anahtar bileşeni. |
      | 4 | `track_name` | `track.name` | `string` | hayır | Anahtar bileşeni. |
      | 5 | `playcount` | `track.playcount` (str→int) | `int64` | hayır | Kümülatif sayaç. Günlük artış = iki snapshot farkı. |
      | 6 | `listeners` | `track.listeners` (str→int) | `int64` | hayır | Kümülatif. `playcount >= listeners` 39/39 doğrulandı. |
      | 7 | `duration_seconds` | `track.duration` (str→int), **`0 → NULL`** | `int32` | evet | 0 = "bilinmiyor". 1.5'in açık sorusu kapandı. |
      | 8 | `track_mbid` | `track.mbid` — anahtar yoksa `None` | `string` | evet | 4/19 kayıtta anahtar **yok**. `.get()` şart. |
      | 9 | `artist_mbid` | `track.artist.mbid` — anahtar yoksa `None` | `string` | evet | Yeniden adlandırma tespitinin tek yolu. |
      | 10 | `track_url` | `track.url` | `string` | hayır | %100 türetilemiyor (35/39). Doğrulama linki. |
      | 11 | `ingested_at` | *türetilmiş* `datetime.now(timezone.utc)` | `timestamp[us, UTC]` | hayır | `snapshot_date`'ten ayrı. ADR-0005. |

      **Reddedilenler — dördü de gerekçeli:**

      | Alan | Sınav | Ölçüm |
      |---|---|---|
      | `streamable.#text`, `streamable.fulltrack` | Varyans | 39/39 kayıtta `{"#text":"0","fulltrack":"0"}`. Sıfır entropi. |
      | `image[]` (4 boyut) | Varyans | **156 URL → 4 tekil**, hepsi Last.fm placeholder'ı (`2a96cbd8...`). Non-null, dolu, tamamen boş. |
      | `artist.url` | Fonksiyonel bağımlılık | `artist_name`'den 39/39 üretilebildi. |
      | `@attr.page/perPage/totalPages/total` | Taşıma mekaniği | `rank`'in **girdisi**, sonucu değil. Raw'da kalır. |

      **1.6'nın birinci borcu kapandı — `rank` nasıl türetilecek.**
      Sıralama payload'da **hiçbir alanda yok** ve hiçbir alandan türetilemiyor. Ölçüm:

      | | idx 0 | idx 1 | idx 4 |
      |---|---|---|---|
      | page=1 `playcount` | 1.114.096 | 13.320.589 | 15.482.186 |
      | page=500 `playcount` | — | 3.531.260 | 7.681.594 |

      `playcount` da `listeners` da azalan sıralı **değil** — üstelik 500. sayfadaki bir
      parçanın `playcount`'u 1. sayfadakinden 7 kat büyük olabiliyor. Yani chart'ın
      sıralama ölçütü response'ta yok. **Bunun sonucu:** `ROW_NUMBER() OVER (ORDER BY
      playcount DESC)` ile sorgu anında türetme alternatifi **ölçümle elendi**; `rank`
      materyalize edilmek zorunda.

      Formül: `rank = (int(attr["page"]) - 1) * int(attr["perPage"]) + index + 1`

      **Global `enumerate` yanlış.** Son sayfa 20 değil **19** kayıt döndü (ölçüldü);
      sayfaları birleştirip baştan numaralandıran kod, eksik dönen her sayfadan sonra tüm
      sıraları bir kaydırır. Her sayfa kendi `@attr.page`'i ile hesaplanmalı.

      **Adım 4'e yazılan borç:** `rank` transform'da hesaplanabilir **ama yalnızca** raw
      katman (1) her sayfayı kendi kaydı olarak, birleştirmeden ve (2) `@attr`'ı atmadan
      saklarsa. Raw bunlardan birini yaparsa `rank` kalıcı olarak kurtarılamaz.
      4.x'te "@attr metadata, veri değil" deyip atmak çok doğal görünecek — görünmesin.

      **1.6'nın ikinci borcu kapandı — `artist.mbid` ölçüldü.**

      | | page=1 | page=500 |
      |---|---|---|
      | `artist.mbid` dolu | 20/20 | 18/19 (1 kayıtta anahtar yok) |
      | `track.mbid` dolu | 20/20 | **15/19** |

      Yani `artist_mbid`, anahtar olarak seçilen `track_mbid`'den **daha eksiksiz**.
      Barış önce "bunu saklamak bir şey kazandırmaz" dedi; ölçüm bunu çürüttü.
      Saklanma gerekçesi: ADR-0005'te **bilerek kabul edilen** tek zayıflık — sanatçı adı
      değişirse geçmiş satırların eski adı taşıması — yalnızca bu alanla fark edilebilir.
      Onsuz "Kanye West" ve "Ye" sonsuza kadar iki ayrı sanatçıdır ve bu geriye dönük
      olarak tespit **bile edilemez**. **Kalıyor.**

      **`track_url` — burada ben (Claude) yanıldım, ölçüm düzeltti.**
      "url zaten `artist_name` + `track_name`'den türetilebilir, atılmalı" dedim. Test:

      ```
      quote_plus ile yeniden üretilebilen: 35 / 39
      ```

      Tutmayan 4 kayıt: Last.fm `(` `)` `$` `,` karakterlerini kaçırmıyor, `quote_plus`
      kaçırıyor. Yani url **Last.fm'in kendi encode kurallarını** taşıyor, RFC'nin değil.
      Türetseydik kayıtların ~%10'unda **sessizce** kırık link üretirdik. **Saklanıyor** —
      ADR-0005'in "url normal kolon olarak kalır" kararıyla da tutarlı.

      **`duration_seconds` için `0 → NULL` kabul edildi.** Gerekçe: belirsizliği veri
      katmanında bir kere çözmek. 0'ı olduğu gibi saklarsan o kolona dokunan *her* sorgu
      `WHERE duration > 0` filtresini hatırlamak zorunda kalır ve biri unutur.

      **Tip kararlarının gerekçeleri** (detay → not 15 §3): `playcount`/`listeners` →
      `int64` çünkü kaynağın kümülatif sayacı, tavanını biz belirlemiyoruz ve Parquet
      encoding sonrası dar tip yer kazandırmıyor, sadece sessiz taşma riski veriyor.
      `duration_seconds` → `int32`, burada dar tip **kasıtlı bir üst sınır ifadesi**.
      `snapshot_date` → `date`, `timestamp` değil: **tip, grain'i ifade eden bir
      sözleşmedir**. Hiçbir kolonda `category` yok — `artist_name` kardinalitesi page=1'de
      6/20, page=500'de 19/19; tek örnekten kategori tipi seçmek klasik hata.

      **`NOT NULL` bir alarm olarak konuldu**, tahmin olarak değil: anahtar bileşenleri ve
      ölçüler boş gelirse **yazma patlamalı**. Bozuk veri erken ve gürültülü patlamalı,
      geç ve sessiz değil.

- [ ] **1.8** Rate limit — **devam ediyor.** Aktif sondaj iptal, kapsam kararı alındı
      (ADR-0006). İki küçük ölçüm kaldı, aşağıda.

      **Header ölçümü — boş sonuç, ama kayda değer bir bulgu.**
      `curl -sS -D - -o /dev/null ... | grep -i -E 'ratelimit|retry-after|x-rate'` →
      **hiçbir şey**. Ne `Retry-After`, ne `RateLimit-*`, ne `X-RateLimit-*`.
      Sonucu: 3.4'teki backoff süresi **istemci tarafında hesaplanacak**, sunucudan
      okunamayacak. Bedava gelen bilgi yoktu, kendimiz üreteceğiz.

      **Belgelenen limit (ikinci el kaynak — birincil ToS sayfası doğrulanmadı):**
      *"saniyede 5 istek, originating IP başına, 5 dakikalık ortalama üzerinden"*,
      artı ayrı bir **frequency cap** maddesi: sürekli saniyede birkaç istek veya ani
      sıçrama, API hesabının askıya alınma sebebi. İki cümle gerilimde — 5/s serbest
      ama "sürekli birkaç/sn" cezalı. Okunuşu: **5/s bir tavandır, hedef değildir.**

      **Kapsam belirsizliği çözüldü: limit IP başına.** 9.7'yi etkiliyor — Lambda'nın
      dönen IP'leri ayrı kova demek, ama ev + iş aynı IP'den giderse aynı kova.
      (Öncesinde iki çelişkili ifade vardı: unofficial docs "your IP", gerçek hata
      metni "this application".)

      **Aktif sondaj yapılmadı — bilinçli.** İki katmanlı gerekçe: (1) doküman sayıyı
      ve kapsamı veriyor, (2) ADR-0006'dan sonra günlük istek ~5, yani limit bağlayıcı
      bir kısıt değil. Sondajın bedeli sıfır değil: aşırı kullanım cezası hata kodu
      **26 — "your API key has been banned"**. Riski olmayan aşamalar cevabı verdiği
      için riskli aşamaya geçilmedi. Protokol → not 17 §2.

      **`limit` parametresi ölçüldü — sayfalama semantiğini değiştiriyor.**

      | İstek | `perPage` | `totalPages` | `total` | kayıt |
      |---|---|---|---|---|
      | `limit=20` | `20` | `500` | `10000` | 20 |
      | `limit=100` | `100` | `100` | `10000` | 100 |

      **1.5'in şüphesi doğrulandı:** `total: 10000` gerçek bir sayım değil, sabit bir
      **tavan**. `totalPages = total / perPage`. İki farklı `limit` ile `total`
      değişmiyor, `totalPages` değişiyor.

      **`rank` üzerindeki sonucu kritik:** `perPage` artık sunucunun sabit bir özelliği
      değil, **bizim gönderdiğimiz bir parametre**. 1.7'de "junior tuzağı" diye yazılan
      *"`perPage`'i 20 diye sabit yazmak"* artık varsayımsal değil — sayfa boyutunu
      değiştiren taraf biziz. Formül `@attr`'dan okunduğu sürece doğru kalır; sabit
      yazılırsa config değiştiği gün **sessizce** bozulur.

      **Kapsam kararı: top 100 → ADR-0006.** Günlük ~500 istek yerine ~5.
      Seçilen yol tek istekle `limit=100` **değil**, hedef sayıya kadar sayfalama.
      Gerekçe: `limit=100` ölçüldü ve bugün çalışıyor, ama doğruluğu kontrol
      etmediğimiz bir sunucu parametresine bağlıyor — Last.fm `limit`'i kırparsa cevap
      **sessizce kısa** gelir, hata fırlamaz. Hedef sayıya kadar döngü, sunucu
      `perPage`'i ne yaparsa yapsın doğru çalışır. Ayrıca sayfalama kodu her koşuda
      birkaç kez çalışır, yani ölü kod olmaz.

      **ROADMAP revize edildi:** 3. adımda sayfalama alt adımı **hiç yoktu** — 3.9
      olarak eklendi. Araya sokulmadı, sona eklendi: `3.7` başka dosyalardan referanslı
      (not 11, PROGRESS 1.2), yeniden numaralamak o bağlantıları sessizce kırar.
      **Numara bir kimliktir, sıra değildir** — ADR'lerin asla yeniden numaralanmama
      gerekçesiyle aynı.

      **Kalan iki ölçüm:**

      1. **Pasif gecikme ölçümü** — 20 ardışık istek (not 17 §2, aşama 3 script'i).
         Amacı limit bulmak değil: 3.2'deki `timeout` değerinin gerçek verisi.
         Timeout'u tahminle koymak yaygın ve yanlış.
      2. **Tarih parametresi testi** — ADR-0005 ve ADR-0006 *"`chart.getTopTracks`
         tarih parametresi almıyor"* varsayımına dayanıyor ve bu **hâlâ ölçülmedi**;
         iddia API dokümanına dayanıyor. Doğruysa backfill yalnızca raw katmandan
         yapılabilir — yani ADR-0006'nın "kaçırılan gün kalıcı kayıptır" maddesi buna
         bağlı. Test: bir tarih parametresi ekleyip cevabın değişip değişmediğine bakmak.

## Açık sorular

- Build backend `setuptools` seçildi; `uv` bir build backend değil (resolver + paket
  yöneticisi), dolayısıyla ADR-0003 bu kararı değiştirmiyor. `hatchling` alternatifi
  açık kalmaya devam ediyor; değişirse ADR yazılır.
- `.python-version` yok. `requires-python = ">=3.11"` bir aralık — iki makinede farklı
  yorumlayıcı seçilebilir (ev: 3.14.5). Sapma görülürse `uv python install` +
  `.python-version` ile sabitlenecek. Şimdilik bilinçli olarak eklenmedi.
- Adım 8.5'te CI'da `uv`'nin **kendi sürümü** sabitlenecek. Bağımlılıkları kilitleyip
  aracı kilitlememek, "kendiliğinden bozulan build" riskini açık bırakır.
- **Chart'ın sıralama ölçütü bilinmiyor.** 1.7'de ölçüldü: sıra ne `playcount` ne
  `listeners` ile uyumlu, 500. sayfada 1. sayfadan büyük `playcount`'lar var. Yani chart
  muhtemelen **son dönem** aktivitesine göre sıralı, `playcount` ise **tüm zamanlar**
  kümülatif. Aynı satırda iki farklı zaman semantiği taşınıyor. Bu bir hata değil ama
  analiz yapılırken (`rank` ile `playcount` birlikte yorumlanırken) bilinmesi gerek.
  Doğrulanamaz — Last.fm ölçütü belgelemiyor. Şema notu olarak kalsın.
- **`rank` bazı SQL lehçelerinde ayrılmış kelime.** Athena/Presto'da `RANK()` bir pencere
  fonksiyonu. Kolon adı olarak sorun çıkarırsa `chart_rank`'e dönülecek. → 9.x'te test.
- **Adım 4'e devredilen borç:** raw katman her sayfayı **ayrı** ve `@attr` ile birlikte
  saklamak zorunda; aksi halde `rank` kalıcı olarak kurtarılamaz hale gelir. Bu bir
  "açık soru" değil, unutulması muhtemel bir **kısıt**. → 4.x.
- **Aynı gün içinde sayfa kayması.** Chart sayfalar çekilirken yeniden sıralanırsa aynı
  parça iki sayfada görünebilir ve anahtar tek `snapshot_date` içinde çakışır. Gözlenmedi
  (iki fixture farklı sayfalar, kesişim yok) ama çürütülmedi de. → 4.5 / 5.8.
- **`chart.getTopTracks` tarih parametresi almıyor** iddiası API dokümanına dayanıyor,
  ölçülmedi. Doğruysa backfill yalnızca raw katmandan yapılabilir. → 1.8.

## Git geçmişinde görünmeyen kararlar

- Veri gölü `/data/` altında yaşar ve gitignore'ludur. Klasör yapısı ileride kurulacak
  S3 yapısını (`raw/`, `curated/`) birebir taklit eder — böylece AWS'ye taşırken yol
  mantığı değişmez.
- `docs/notes/` Türkçe (öğrenme defteri), `docs/adr/` İngilizce (portfolyo çıktısı).
- `PROJECT_CONTEXT.md` Claude proje bilgisinden repoya taşındı. Tek kaynak burasıdır.

## Sonraki oturum için hatırlatma

- Oturuma `git pull` ile başla, `git push` ile bitir. İki makinede çalışılıyor.
- `git pull` sonrası `git status` **temiz** olmalı. Kirliyse `.gitattributes` o makinede
  uygulanmamış demektir — `git ls-files --eol` ile bak.
- **`uv` her iki makinede de kurulu** (ev + iş). Yeni bir makinede `uv sync` şart.
- **`.env` git'e girmez** — her makinede elle oluşturulur. Yeni makinede ilk iş:
  `.env.example`'ı kopyalayıp gerçek key'i yazmak.
- `curl` çağrılarından önce `.env`'i oturuma yükle (`docs/notes/11` §3). Sır komut
  satırına elle yazılmaz.
- Adım 1 kod adımı **değil**. Çıktısı: kaydedilmiş gerçek payload + hata payload'ı +
  grain cümlesi + hedef şema tablosu. Kod yazma isteği gelirse Adım 3'e ait demektir.

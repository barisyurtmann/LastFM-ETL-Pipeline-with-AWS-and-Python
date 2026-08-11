# Progress

Bu dosya projenin **tek durum kaynağıdır**: sadece *nerede olduğumu* tutar.
Her oturumun başında okunur, her alt adımın sonunda güncellenir.

> **Plan burada değildir.** Alt adım listesi, "bitti" tanımları ve bağımlılıklar için
> → [`ROADMAP.md`](ROADMAP.md)

Kural: bu dosya yalan söyleyebilir (güncellemeyi unutursan). `git log --oneline` söyleyemez.
Çelişki varsa git haklıdır.

---

**Last updated:** 2026-08-11 (iş bilgisayarı)
**Current step:** 1 — Veriyi tanı ([plan](ROADMAP.md#adım-1--veriyi-tanı))
**Next sub-step:** 1.6 — Grain kararı: "Bir satır = ..." cümlesini kurmak

> **ADIM 0 TAMAMLANDI.** Bitti tanımının beş maddesi de doğrulandı (aşağıda).
> **1.1, 1.2, 1.3, 1.4, 1.5 TAMAMLANDI.**

**1.6'nın girdisi — 1.5'te ölçülen ve grain kararını doğrudan etkileyen üç şey:**
`mbid` kuyrukta %21 boş (anahtar adayı ama tek başına yetmiyor), aynı sanatçının birden
fazla parçası aynı payload'da geliyor (sanatçı boyut mu, kolon mu?), ve payload'da
**tarih alanı yok** — çekildiği gün dışarıdan eklenmek zorunda.

**Adım 1 hatırlatması:** bu adımın çıktısı kod değil, **bilgi ve örnek dosya**. Kod yazma
isteği gelirse Adım 3'e aittir.

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

## Açık sorular

- Build backend `setuptools` seçildi; `uv` bir build backend değil (resolver + paket
  yöneticisi), dolayısıyla ADR-0003 bu kararı değiştirmiyor. `hatchling` alternatifi
  açık kalmaya devam ediyor; değişirse ADR yazılır.
- `.python-version` yok. `requires-python = ">=3.11"` bir aralık — iki makinede farklı
  yorumlayıcı seçilebilir (ev: 3.14.5). Sapma görülürse `uv python install` +
  `.python-version` ile sabitlenecek. Şimdilik bilinçli olarak eklenmedi.
- Adım 8.5'te CI'da `uv`'nin **kendi sürümü** sabitlenecek. Bağımlılıkları kilitleyip
  aracı kilitlememek, "kendiliğinden bozulan build" riskini açık bırakır.

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

# 15 — Şema tasarımı: alan eleme, tip seçimi, isimlendirme

> **Bu not neden var?** 1.7'de "hedef şema taslağı" çıkarırken asıl öğrenilen şey tablonun
> kendisi değil, tabloyu üreten **karar mantığı** oldu. Tablo Last.fm'e özel; mantık değil.
> Bu not, bir sonraki projede yeni bir kaynakla (API, CSV dökümü, başkasının veritabanı)
> karşılaştığında açıp sırayla uygulayacağın kural setidir.
>
> Örnekler Last.fm'den, çünkü ölçülmüş gerçek veri. Kurallar kaynaktan bağımsız.

---

## 0. Şemaya başlamadan önce: raw katman ≠ curated katman

Alan elemeye başlamadan önce bu ayrım oturmalı, çünkü **eleme cesaretinin kaynağı budur**.

| | Raw katman | Curated katman |
|---|---|---|
| Cevapladığı soru | "Kaynak o gün bana tam olarak ne gönderdi?" | "Bu veriyle hangi soruları soracağım?" |
| İçerik | Payload olduğu gibi, byte düzeyinde | Yorumlanmış, elenmiş, tiplenmiş |
| Alan atılır mı | **Asla** | Evet, gerekçeli |
| Tip dönüşümü | Yok | Var |
| Kime hizmet eder | Geleceğe, denetime, yeniden işlemeye | Sorguya, rapora, analize |
| Değişirse | Değişmez, immutable | Yeniden üretilebilir |

**Junior refleksi:** "veri kaybetmeyeyim" diye payload'daki her alanı hedef tabloya koymak.

Refleks doğru, katman yanlış. Veri kaybetmemenin yeri **raw katmandır**. Curated bir arşiv
değil, bir **yorumdur** — ve her yorumun bir tezi olmalı. Curated'daki her kolonun cevap
verdiği bir soru olmak zorunda; yoksa o kolon disk yer, sorgu yavaşlatır, dokümantasyon
borcu yaratır ve okuyan herkese "bu ne işe yarıyor" diye sordurur.

**Sonuç — akılda kalması gereken cümle:**

> Raw katman yoksa hiçbir alanı elemeye hakkın yok, çünkü karar geri dönülemez.
> Raw katman varsa eleme kararlarının neredeyse hepsi ucuzdur.

Bu tek cümle, aşağıdaki 4. sınavın (geri dönülebilirlik) tüm gerekçesidir.

---

## 1. Bir alanı şemaya almanın dört sınavı

Payload'daki **her** alana sırayla sorulur. Herhangi birinde takılırsa alan curated'a
girmez — ama raw'da durmaya devam eder.

| # | Sınav | Sorusu | Takılırsa |
|---|---|---|---|
| 1 | Varyans | Her satırda aynı değer mi? | Bilgi taşımıyor |
| 2 | Fonksiyonel bağımlılık | Başka kolondan deterministik türetilebilir mi? | Aynı bilgiyi iki yerde tutuyorsun |
| 3 | Taşıma mekaniği | Verinin kendisi mi, sana ulaşma biçimi mi? | Modeli kaynağın iç yapısına bağlıyorsun |
| 4 | Geri dönülebilirlik | Kaybedersem raw'dan geri gelir mi? | Karar geri dönülemez, çok daha dikkatli ol |

İlk üçü **"almama" gerekçesi** üretir. Dördüncüsü gerekçe üretmez, **riski ölçer**: aynı
karar 4. sınavı geçiyorsa ucuz, geçmiyorsa pahalıdır.

---

### Sınav 1 — Varyansı var mı?

**Soru:** Bu kolonun tekil değer sayısı kaç?

Tek bir tekil değer varsa kolon hiçbir satırı diğerinden ayırmıyor demektir. Bilgi
kuramında bu sıfır entropi; pratikte "her satırda 'evet' yazan bir kolon".

**Nasıl ölçülür:**

```python
# One line tells you which columns carry zero information.
df.nunique().sort_values()
```

Ham JSON üzerinde, DataFrame'e girmeden:

```python
from collections import Counter
Counter(json.dumps(r.get("streamable"), sort_keys=True) for r in records)
```

> `json.dumps(..., sort_keys=True)` neden? Çünkü `streamable` bir dict ve dict'ler
> hashlenemez — `Counter`'a doğrudan giremezler. `sort_keys=True` olmadan aynı içerikli iki
> dict farklı string üretebilir ve sahte varyans görürsün.

**Last.fm'de ne çıktı:**

```
39 kaydın 39'unda: {"#text": "0", "fulltrack": "0"}
```

Tek bir farklı değer yok. Last.fm bu alanı yıllar önce anlamsızlaştırmış ama API
sözleşmesini bozmamak için göndermeye devam ediyor. **Reddedildi.**

**Genel ders:** Bir API'nin alanı göndermesi, o alanın bilgi taşıdığı anlamına gelmez.
Olgun API'lerin çoğunda "eskiden bir şey ifade eden, artık etmeyen" alanlar vardır —
kaldırmak geriye dönük uyumluluğu bozacağı için sonsuza kadar gönderilirler. Bunlara
**vestigial field** (körelmiş alan) denir. Sadece ölçüm ayırt eder.

**Tuzak — "şimdilik sabit" ile "her zaman sabit" farkı.** Elindeki örneklem küçükse sıfır
varyans yanıltıcı olabilir. Ölçütün: *bu alanın değişebileceği bir senaryo tarif
edebiliyor muyum?* `streamable` için tarif edilebilir bir senaryo yok (Last.fm streaming'i
kapattı). Ama örneğin bir `country` alanı örneklemde tek ülke gösteriyorsa bu sıfır varyans
değil, **dar örneklemdir** — elemezsin.

---

### Sınav 2 — Başka kolondan türetilebilir mi?

**Soru:** A kolonunun her değeri için B kolonu tek bir değer alıyor mu?

Alıyorsa B, A'ya **fonksiyonel olarak bağımlıdır** (`A → B`). B'yi saklamak aynı bilgiyi
iki yerde tutmaktır; iki yerde tutulan her bilgi eninde sonunda **birbirinden sapar**.

**Nasıl ölçülür:**

```python
# If max == 1, then A determines B: A -> B is a functional dependency.
df.groupby("A")["B"].nunique().max()
```

Türetme kuralı deterministik bir fonksiyonsa (URL encoding, string birleştirme, tarih
formatlama) doğrudan test edilir:

```python
guess = f"https://www.last.fm/music/{quote_plus(artist)}"
guess == record["artist"]["url"]
```

**Last.fm'de ne çıktı — iki farklı sonuç, ikisi de öğretici:**

| Alan | Test | Sonuç | Karar |
|---|---|---|---|
| `artist.url` | `artist_name`'den üretilebiliyor mu | **39/39 evet** | Reddedildi |
| `track.url` | `artist_name` + `track_name`'den üretilebiliyor mu | **35/39** | **Saklandı** |

`track.url` neden tutmadı? Last.fm bazı karakterleri kaçırmıyor, standart kütüphane
kaçırıyor:

| Karakter | Last.fm | Python `quote_plus` |
|---|---|---|
| `(` `)` | `(` `)` | `%28` `%29` |
| `$` | `$` | `%24` |
| `,` | `,` | `%2C` |

Yani `url` alanı **Last.fm'in kendi encode kurallarını** taşıyor, RFC 3986'nın değil.
Türetmeye kalksaydım kayıtların ~%10'unda kırık link üretirdim — ve **sessizce**, çünkü
string üretimi hata fırlatmaz.

**Genel ders — bu notun en pahalı dersi:**

> Fonksiyonel bağımlılık bir **hipotezdir**, göz kararı doğrulanmaz. "Bu zaten şundan
> türetilebilir" cümlesini kurduğun her seferde, kuralı yazıp tüm kayıtlar üzerinde
> karşılaştır. %90 tutan bir kural, tutmayan %10'da sessiz bozulma üretir.

**Alt kural — türetme maliyeti de sayılır.** Bir alan teknik olarak türetilebiliyor ama
türetmesi pahalıysa (başka tabloya join, dış servise çağrı, ağır hesap) saklamak
meşrudur. Buna kasıtlı **denormalizasyon** denir ve analitik şemalarda normal bir
tercihtir — normalizasyon OLTP'nin (işlem sistemleri) erdemidir, OLAP'ın (analitik) değil.
Ama kasıtlı olmalı: "unuttum" ile "karar verdim" arasındaki fark, şemanın yanında yazan
gerekçedir.

---

### Sınav 3 — Verinin kendisi mi, taşıma mekaniği mi?

**Soru:** Bu alan gözlemlediğim olgu hakkında mı, yoksa olgunun bana **ulaşma biçimi**
hakkında mı?

Taşıma mekaniği (transport metadata) örnekleri, kaynak türüne göre:

| Kaynak | Taşıma mekaniği olan alanlar |
|---|---|
| REST API | `page`, `perPage`, `totalPages`, `next_cursor`, `request_id`, `rate_limit_remaining` |
| CSV dökümü | satır numarası, dosya adı, dosya sırası |
| Kafka | partition, offset, topic |
| Veritabanı replikasyonu | `_binlog_position`, `_lsn` |
| Web scraping | HTML sınıf adları, DOM sırası |

Bunlar curated'a girmez. **Ama raw'da mutlaka kalır** ve çoğu zaman transform'a **girdi**
olurlar — sonra atılırlar.

**Last.fm'de:** `@attr.page` ve `@attr.perPage` `rank` hesabının girdisi. `rank` üretilir,
`@attr` atılır. Girdi olmak, sonuçta yer almayı gerektirmez.

**Genel ders:** Bir alanı curated'a koymak, veri modelini kaynağın **iç yapısına** bağlar.
Last.fm sayfa boyutunu 20'den 50'ye çıkardığı gün `page` kolonu anlamsızlaşır ve geçmiş
veriyle karşılaştırılamaz hale gelir. Model, kaynağın *ne söylediğine* bağlanmalı, *nasıl
söylediğine* değil.

**Sınır durumu — ne zaman saklanır?** Taşıma metadata'sı **veri kalitesi sorununu teşhis
etmek** için saklanabilir: hangi dosyadan/hangi çekimden geldiği (`source_file`,
`ingest_run_id`). Buna **lineage** (soy) kolonu denir ve büyük pipeline'larda standarttır.
Ölçüt: *bu kolon bir analiz sorusuna mı, yoksa bir hata ayıklama sorusuna mı hizmet
ediyor?* İkincisiyse meşru ama ayrı bir kategori — ve küçük projede erken eklenirse
over-engineering olur.

---

### Sınav 4 — Kaybedersem geri gelir mi?

**Soru:** Bu alanı curated'dan çıkarırsam, gelecekte gerekirse geri getirebilir miyim?

| Cevap | Ne demek | Nasıl davranılır |
|---|---|---|
| Evet, raw'dan yeniden işlerim | Karar **geri dönülebilir** | Şüphedeysen çıkar. Geri getirmek ucuz. |
| Hayır, kaynak bir daha o veriyi vermez | Karar **geri dönülemez** | Şüphedeysen sakla. Yanılma bedeli sonsuz. |

Bu sınav bir alanı elemez; **eleme kararının riskini fiyatlar**. İlk üç sınavın verdiği
"hayır" cevabına ne kadar güveneceğini belirler.

**Last.fm'de:** Raw katman payload'ı olduğu gibi sakladığı için tüm eleme kararları geri
dönülebilir. Bu yüzden `image`, `streamable`, `artist.url` rahatça çıkarıldı.

**Kritik uyarı:** Bu geri dönülebilirlik **tamamen** raw katmanın payload'ı *bozmadan*
saklamasına bağlı. Raw bir gün "biraz temizlenmiş", "gereksiz alanları atılmış" hale
gelirse bu kapı sessizce kapanır — ve kapandığını yıllar sonra, bir alana ihtiyaç
duyduğunda fark edersin.

> **Raw katmanın tek kuralı:** yorumlama. Sıkıştır, böl, partition'la, ama **değiştirme**.

---

## 2. Null'ın yedi kılığı

Bu, alan eleme kadar sık lazım olan ve neredeyse hiç öğretilmeyen konu. "Veri yok"
durumunun kaynaklarda aldığı biçimler:

| # | Kılık | Python'da görünüşü | Nasıl yakalanır |
|---|---|---|---|
| 1 | **Anahtar hiç yok** | `r["mbid"]` → `KeyError` | `"mbid" not in r` |
| 2 | Gerçek null | `None` | `r.get("mbid") is None` |
| 3 | Boş string | `""` | `r.get("mbid") == ""` |
| 4 | Beyaz boşluk | `"   "` | `not str(v).strip()` |
| 5 | **Sentinel sayı** | `0`, `-1`, `9999`, `1900-01-01` | Dağılıma bak: uç değerde yığılma var mı |
| 6 | **String'e gömülü null** | `"null"`, `"NULL"`, `"None"`, `"N/A"`, `"-"` | `v.lower() in {"null","none","n/a","-"}` |
| 7 | **Placeholder içerik** | Varsayılan görsel, `"Unknown Artist"`, `"noreply@"` | **Tekil değer sayısı** |

**1, 2 ve 3 aynı şey değil** — Last.fm'de ölçüldü:

```
track.mbid  → anahtar yok: 4  |  boş string: 0  |  dolu: 15
```

Yani `mbid` "boş" değil, **eksik**. Kod farkı somut:

```python
r["mbid"]            # KeyError -> pipeline crashes
r.get("mbid")        # None     -> correct
r.get("mbid", "")    # ""       -> invents a value the source never sent
```

Üçüncüsü en sinsisi: kaynağın hiç göndermediği bir değeri **sen uyduruyorsun**. Sonra altı
ay sonra "neden bu kadar çok boş string var" diye araştırırken kendi kodunu buluyorsun.

**5 ve 7 en tehlikelileri, çünkü hiçbir null kontrolünden geçmezler.**

### Kılık 5 — sentinel sayı (Last.fm: `duration == 0`)

```
page=500 → duration min=0, sıfır sayısı=2
```

Parça 0 saniye mi, süre bilinmiyor mu? API ayırt etmiyor. `AVG(duration)` hesabı bu 0'ları
gerçek süre sanar ve **sessizce yanlış** cevap verir.

**Karar:** transform'da `0 → NULL`. Gerekçe: yorumu bir kere, doğru yerde yapmak. 0'ı
olduğu gibi saklarsan, o kolona dokunan **her** sorgu aynı `WHERE duration > 0` filtresini
hatırlamak zorunda kalır — ve biri unutur. Unutan kişi genelde altı ay sonraki sensin.

> **Genel kural:** Belirsizliği veri katmanında çöz, sorgu katmanında değil. Sorgu katmanı
> N kişi ve N farklı hatırlama olasılığıdır; veri katmanı bir yer ve bir karardır.

**Sentinel avlama yöntemi:** her sayısal kolonun **min, max ve en sık 5 değerini** yazdır.
Sentinel'ler uç değerde anormal yığılma olarak görünür — `0` sayısının %8 olması doğal bir
dağılım değildir.

### Kılık 7 — placeholder içerik (Last.fm: `image`)

```
156 URL (39 kayıt × 4 boyut) → 4 tekil URL
Hepsinin hash'i aynı: 2a96cbd8b46e442fc41c2b86b821562f
```

Bu Last.fm'in "resim yok" varsayılan görselidir. Alan **dolu, string, non-null**, her
şemayı geçer — ve tamamen boştur.

**Bunu yakalayan tek şey tekil değer sayısıdır.** `isna()`, `NOT NULL`, `COUNT(*)`,
`len(v) > 0` — hiçbiri görmez.

> **Refleks haline getir:** yeni bir kaynakta *her* kolon için `nunique()` çalıştır ve
> `nunique / count` oranına bak. Oran beklenenden düşükse ya kılık 7 vardır ya da kolon
> aslında kategoriktir. İkisi de bilmen gereken şeyler.

---

## 3. Tip seçimi

Tip bir depolama detayı değil, **veri hakkında verdiğin bir sözdür**. `date` seçmek
"gün içi fark anlamsızdır" demektir; `int32` seçmek "bu değer 2.1 milyarı geçmez"
demektir. Söz tutulmazsa sistem ya patlar ya sessizce yalan söyler.

### Sayılar

| Durum | Seçim | Gerekçe |
|---|---|---|
| **Kümülatif sayaç**, kaynağın kontrolünde (`playcount`, `view_count`, `total_bytes`) | En geniş int (`int64`) | Tavanı sen belirlemiyorsun. Taşma sessizdir. |
| **Sınırlı büyüklük**, doğası gereği sınırlı (`duration_seconds`, `age`, `score`) | Dar int (`int32`/`int16`) | Dar tip burada **bilinçli bir üst sınır ifadesidir**, tasarruf değil. |
| **Para** | **Asla `float`.** `decimal` ya da tam sayı olarak en küçük birim (kuruş/cent) | `0.1 + 0.2 != 0.3`. IEEE 754 ikili kesir, ondalık parayı temsil edemez. |
| **Oran, ölçüm, olasılık** | `float64` | Zaten yaklaşık bir büyüklük. |
| **Kimlik** (`id`, `mbid`, sipariş no) | **`string`**, sayısal görünse bile | Baştaki sıfırlar kaybolur (`007` → `7`), aritmetik anlamsızdır, kaynak bir gün harf ekler. |

> **Kimlik kuralı sık ihlal edilir ve pahalıya patlar.** Posta kodu, TCKN, ürün kodu,
> telefon — hepsi sayısal görünür, hiçbiri sayı değildir. Test: *bu değerlerin ortalamasını
> almak anlamlı mı?* Değilse sayı değil, string.

**Neden dar tiple yer kazanmaya çalışmıyoruz?** Parquet gibi sütunlu formatlar sayıları
delta + RLE + dictionary ile zaten sıkıştırır. `int64` ile `int32` arasındaki fiziksel fark
sıkıştırma sonrası çoğu zaman ihmal edilebilir. Yani dar tip seçmek **yer kazanmaz**, sadece
taşma riski alır. Kazanç yokken risk alınmaz.

### Tarih ve saat

| Durum | Seçim | Gerekçe |
|---|---|---|
| Grain gün ise | `date` | `timestamp` kullanmak "gün içi saat anlamlıdır" demektir — yalan olur ve anahtarı bozar. |
| Gerçek an | `timestamp` **tz bilgisiyle** | Naive timestamp 6 ay sonra "bu hangi dilim" sorusuna cevap veremez. |
| Üretimi | `datetime.now(timezone.utc)` | `datetime.utcnow()` **naive** döner — UTC değeri taşır, UTC olduğu bilgisini taşımaz. Python 3.12'de deprecate edildi. |
| Yerel saat | Neredeyse hiçbir zaman | `date.today()` çalıştığı makinenin dilimini kullanır; ev/iş/Lambda üç farklı sonuç verir. |

> **Tip, grain'i ifade eden bir sözleşmedir.** Bu cümle `date` vs `timestamp` seçiminin
> tamamıdır.

### Metin ve kategori

**Düşük kardinaliteli bir metin kolonunu `category`/`enum` yapmadan önce iki kez ölç.**
Last.fm'de:

```
artist_name tekil sayısı → page=1: 6/20   |   page=500: 19/19
```

Aynı kolon, aynı gün, farklı sayfa. Kardinalite **verinin nereden alındığına** göre
değişiyor. Tek örnekten kategori tipi seçmek klasik hatadır: chart'ın popüler ucunda az
sanatçı çok parça, kuyrukta her parça farklı sanatçı.

Ayrıca `category` tipi bir **taahhüttür**: yeni değer geldiğinde ya hata verir ya sessizce
`NaN` üretir (kütüphaneye göre değişir — ikisi de kötü sürpriz). Parquet'in dictionary
encoding'i aynı depolama kazancını **taahhüt vermeden** sağlar. Yani `category` tipini
performans için değil, yalnızca **değer kümesi gerçekten kapalıysa** (cinsiyet kodu, ülke
kodu, durum enum'ı) kullan.

---

## 4. `NOT NULL` bir performans ayarı değil, bir alarmdır

Bir kolona `NOT NULL` koymak "burası hiç boş olmayacak" tahmini değil, **"boş gelirse
yazma işlemi patlasın"** talimatıdır.

| Kolon | Kısıt | Boş gelirse ne olsun |
|---|---|---|
| Anahtar bileşenleri (`snapshot_date`, `artist_name`, `track_name`) | `NOT NULL` | **Patla.** Anahtarsız satır yazmak, tekilliği sessizce bozar. |
| Ölçüler (`playcount`, `listeners`) | `NOT NULL` | **Patla.** Kaynak sayaç göndermiyorsa API bozulmuştur, bilmen gerekir. |
| Gerçekten opsiyonel olanlar (`track_mbid`, `duration_seconds`) | nullable | Sorun yok, ölçüldü, eksik olabiliyor. |

**Arkasındaki ilke, bu notun ikinci en önemli cümlesi:**

> Bozuk veri **erken ve gürültülü** patlamalı; **geç ve sessiz** değil.

Alternatifi şudur: `artist_name` bir gün boş gelir, satır yazılır, anahtar çakışır,
`playcount` farkı bozulur, altı ay sonra bir rapor tuhaf görünür ve nedenini bulmak
haftalar alır. `NOT NULL` bu zincirin ilk halkasında durur ve sana **o gün** söyler.

**Nasıl uygulanır (sırayla, ucuzdan pahalıya):** Pydantic/dataclass şeması → Parquet şeması
(`pyarrow.schema` ile `nullable=False`) → veritabanı `NOT NULL` → ayrı bir veri kalitesi
kontrolü. Küçük projede ilk ikisi yeter.

---

## 5. İsimlendirme

| Kural | İyi | Kötü | Neden |
|---|---|---|---|
| `snake_case` | `track_name` | `trackName` | SQL motorlarının çoğu tırnaksız identifier'ı küçültür; camelCase her sorguda tırnak ister. |
| **Birim adın içinde** | `duration_seconds`, `size_bytes`, `price_usd` | `duration`, `size`, `price` | Birimsiz sayısal kolon = altı ay sonra "saniye mi ms mi" tartışması. |
| Zaman soneki | `ingested_at` (an), `snapshot_date` (gün) | `ingested`, `snapshot` | Ad, tipi ele versin. |
| Boolean öneki | `is_active`, `has_mbid` | `active`, `mbid_flag` | Adı okuyunca true/false olduğu anlaşılsın. |
| **Düzleştirince bağlam ekle** | `artist_mbid`, `track_mbid` | `mbid` (iki tane var) | İç içelikte bağlam yoldan gelir (`artist.mbid`); düzleştirince kaybolur, ada taşınmalı. |
| Kaynak adını körü körüne kopyalama | `track_name` | `name` | Bir join'den sonra hangi tablonun `name`'i olduğu belirsiz. |
| Kısaltma yok | `listeners` | `lstnr`, `cnt` | Kısaltma yazan bir kişiye, okuyan yüz kişiye maloluyor. |
| Ayrılmış kelime yok | `track_rank` gerekirse | `rank`, `order`, `group`, `user` | Bunlar birçok SQL lehçesinde ayrılmış kelime. (`rank` bu projede tek başına kullanılıyor; Athena'da sorun çıkarsa yeniden adlandırılacak.) |

> Bunların hiçbiri resmî bir spesifikasyon değil — **yerleşik sektör pratiği**. İkisi
> farklı şeyler. Bir ekip farklı bir konvansiyon seçebilir; seçilmemesi ve herkesin kendi
> bildiğini yapması kötüdür, konvansiyonun kendisi değil.

---

## 6. Sıra bir veri değildir — ta ki bir kolona yazılana kadar

Bu, 1.7'de ortaya çıkan ve genelleştirilebilir en değerli konu.

**Problem:** Bazı kaynaklarda bilgi, alanlarda değil **dizinin sırasında** durur.
Last.fm chart'ında sıralama hiçbir alanda yok:

| | idx 0 | idx 1 | idx 4 |
|---|---|---|---|
| page=1 `playcount` | 1.114.096 | 13.320.589 | 15.482.186 |
| page=500 `playcount` | — | 3.531.260 | 7.681.594 |

`playcount` da `listeners` da azalan sıralı **değil** — üstelik 500. sayfadaki bir parçanın
`playcount`'u 1. sayfadakinden büyük olabiliyor. Yani chart'ın sıralama ölçütü response'ta
**yok**. Kaybedilirse hiçbir kolondan geri hesaplanamaz.

**Sıranın kod doğru olsa bile öldüğü yerler:**

| Nerede | Neden |
|---|---|
| Paralel çekim | `as_completed` sonuçları **tamamlanma sırasına** verir. `asyncio.gather` sırayı korur, `as_completed` korumaz. |
| Dosya listeleme | `S3 ListObjectsV2` ve `Path.glob` **sözlükseldir**: `page_1, page_10, page_100, page_2`. |
| SQL / Parquet okuma | `ORDER BY`'sız `SELECT` **sırasız bir kümedir** — SQL'in tanımı gereği. Parquet dosya *içinde* sırayı korur, motor korumaz. |
| Partition'a yazma | Bir partition birden fazla dosyaya bölünürse dosyalar arası sıra yoktur. |
| DataFrame işlemleri | `groupby`, `merge`, `drop_duplicates`, `set()` — hiçbiri sıra sözü vermez. |

**Çözüm — genel kalıp:**

> Ordinal'i, kaynağın hâlâ garanti ettiği **en erken sınırda** materyalize et.

Buradaki en erken sınır: JSON array'inin parse edildiği an. Çünkü JSON spec'i **array**
sırasını garanti eder (object anahtar sırasını etmez) ve sayfalama bilgisi tam o anda
elinin altındadır.

```python
rank = (int(attr["page"]) - 1) * int(attr["perPage"]) + index + 1
```

**Neden global `enumerate` değil?** Ölçüldü: son sayfa 20 değil **19** kayıt döndü.
Sayfaları birleştirip baştan sona numaralandırırsan, eksik dönen her sayfadan sonraki tüm
sıralar bir kayar. Her sayfa **kendi `page` değeriyle** hesaplanmalı.

**Junior tuzağı:** `perPage`'i 20 diye sabit yazmak. Kaynak 50'ye çıkardığı gün tüm
sıralar kayar, hiçbir istisna fırlamaz, pipeline yeşil kalır.

**Aynı problemin diğer görünümleri:** CSV'de satır numarasının anlam taşıması, log
dosyalarında olay sırası, sayfalanmış API'lerde ilk-N mantığı, versiyonlanmış kayıtlarda
"en son" tanımı. Hepsinde aynı çözüm: sırayı bir kolona yaz.

---

## 7. Yanıldığım / yanıldığımız yerler

Bu bölüm bu notun en çok işe yarayacak kısmı — altı ay sonra "bunu neden böyle yaptık"
sorusunun cevabı burada.

**Önce şöyle sandım:** `url` alanı `artist_name` ve `track_name`'den türetilebilir,
fonksiyonel bağımlılık sınavında takılır, atılmalı.
**Aslında:** 39 kaydın 4'ünde tutmadı. Last.fm `( ) $ ,` karakterlerini kaçırmıyor,
`quote_plus` kaçırıyor. Türetseydim kayıtların ~%10'unda sessizce kırık link üretirdim.
**Ders:** "Zaten türetilebilir" bir hipotezdir. Kuralı yaz, tüm kayıtlarda karşılaştır,
sonra karar ver. Deneyimli olmak ölçmemek için gerekçe değil.

**Önce şöyle sandım (1.5):** `mbid` kayıtların %21'inde **boş**.
**Aslında (1.6):** Boş değil, **eksik** — anahtar dict'te hiç yok. `""` riski yok, `None`
riski var. `if mbid == "":` dalı hiç yazılmayacak.
**Ders:** "Boş" kelimesi en az yedi farklı teknik durumu gizler (§2). Hangisi olduğunu
söylemeyen bir ölçüm, ölçüm değildir.

**Önce şöyle sandım:** `artist_mbid` bir işe yaramaz, atılabilir.
**Aslında:** Payload'daki **en dolu** kimlik alanı (39'da 38), anahtar yaptığımız
`track_mbid`'den (39'da 35) daha eksiksiz. Ve grain kararında bilerek kabul edilen tek
zayıflığın — sanatçı adı değişirse geçmiş satırların eski adı taşıması — fark
edilebileceği **tek** alan. Onsuz "Kanye West" ve "Ye" sonsuza kadar iki ayrı sanatçıdır
ve bu geriye dönük olarak tespit bile edilemez. **Saklandı.**
**Ders:** "Bir işe yaramaz" ölçülmemiş bir varsayımdır. Doğru gerekçe "raw'dan geri
gelebilir" (4. sınav) olurdu — biri ölçüm, diğeri tahmin.

**Önce şöyle sandım:** `image` alanı dolu, saklanabilir.
**Aslında:** 156 URL → 4 tekil, hepsi placeholder. Non-null, string, her şemayı geçiyor,
tamamen boş.
**Ders:** Doluluk oranı bir kalite ölçüsü değildir. Tekil değer sayısına bak.

---

## 8. Yeni bir kaynakla karşılaştığında: kontrol listesi

Bir sonraki projede sırayla:

**Ölçüm (kod yazmadan önce)**

- [ ] Payload'ı diske kaydet — başarı **ve** hata yolu ayrı ayrı
- [ ] En az **iki farklı yerden** örnek al (ilk sayfa + son sayfa, ilk gün + rastgele gün).
      İlk sayfa veri kalitesinin en yüksek olduğu yerdir; **seçim yanlılığı** kural, istisna değil.
- [ ] Tüm yaprak yolları çıkar: yol, tip, örnek değer
- [ ] Her kolon: `count`, `nunique`, `nunique/count`, `min`, `max`, en sık 5 değer
- [ ] Null'ın yedi kılığını ayrı ayrı say (§2) — "boş" diye tek sayı yazma
- [ ] Anahtar adaylarını test et: tekil mi, hepsi dolu mu, zaman içinde sabit mi
- [ ] Sıra bilgisi taşıyan bir şey var mı — varsa hangi alandan türetilebiliyor, türetilemiyorsa materyalize et

**Karar**

- [ ] Grain'i tek cümleyle yaz: "Bir satır = ..."
- [ ] Birincil anahtarı seç — **az alanla**; alan eklemek anahtarı güçlendirmez, grain'i inceltir
- [ ] Her alanı 4 sınavdan geçir, **reddedilenleri de gerekçesiyle tabloya yaz**
- [ ] Tipleri §3'e göre seç, her birinin verdiği "sözü" kontrol et
- [ ] `NOT NULL` kısıtlarını "burası patlamalı mı" sorusuyla koy, tahminle değil
- [ ] İsimleri §5'e göre gözden geçir

**Doğrulama**

- [ ] Yaprak yol listesindeki **her** yol ya şemada ya reddedilenler listesinde — sessizce atlanan yok
- [ ] "Bu pipeline'ı aynı gün iki kere çalıştırsam ne olur?" — cevabı anahtar veriyor mu
- [ ] "Bu kod prod'da 3 ay çalışsa nerede patlar?" — en az üç senaryo yaz
- [ ] Kararı ADR'ye, genel öğrenmeyi nota yaz

---

## 9. Mülakat cevapları

**"Bir kaynaktaki tüm alanları saklar mısın?"**

> Raw katmanda evet, byte düzeyinde ve yorumlamadan. Curated'da hayır — orada her kolonun
> cevap verdiği bir soru olmalı. Eleme kriterlerim varyans, fonksiyonel bağımlılık, taşıma
> mekaniği ve geri dönülebilirlik. Somut bir örnek: son projemde bir görsel URL alanı %100
> dolu görünüyordu, null kontrollerinin hepsinden geçiyordu — ama 156 değerin sadece 4'ü
> tekildi ve hepsi kaynağın "görsel yok" varsayılanıydı. Doluluk oranı yakalayamıyordu,
> tekil değer sayısı yakaladı.

**"Sıralama bilgisini dağıtık bir pipeline'da nasıl korursun?"**

> Sıralama bir tablonun sahip olduğu bir özellik değildir — `ORDER BY`'sız bir sorgu
> tanım gereği sırasız bir küme döner. Bu yüzden ordinal'i, kaynağın hâlâ garanti ettiği
> en erken sınırda bir kolona yazarım. JSON'da bu, array'in parse edildiği andır.

**"Neden `int64` kullandın, `int32` yetiyordu?"**

> Çünkü o kolon bir kaynak sistemin kümülatif sayacı ve tavanını ben belirlemiyorum.
> Parquet'te delta ve RLE encoding sonrası iki tipin fiziksel farkı ihmal edilebilir —
> yani dar tip bana yer kazandırmıyor, sadece sessiz taşma riski veriyor. Kazanç yokken
> risk almam. Ama `duration_seconds` için `int32` kullandım: orada dar tip bir tasarruf
> değil, kasıtlı bir üst sınır ifadesi.

---

## İlgili

- ADR-0004 — gerçek payload'ların fixture olarak saklanması (bu notun ölçüm verisi)
- ADR-0005 — grain kararı (bu notun anahtar tartışmasının kaynağı)
- Not 13 — veri kaynağı keşif protokolü (ölçümün *nasıl* yapılacağı)
- Not 14 — grain ve fact tabloları (bu notun *öncesi*)

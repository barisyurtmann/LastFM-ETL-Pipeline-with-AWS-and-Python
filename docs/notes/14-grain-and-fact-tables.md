# 14 — Grain, fact table türleri ve anahtar seçimi

**Adım:** 1.6
**Proje kararı için:** [ADR-0005](../adr/0005-define-the-data-grain-as-a-daily-chart-snapshot.md)

Bu not genel bilgidir — Last.fm'e özel değil, her veri modelinde geçerli.

Notun yapısı: **kavram** (§1–7) → **protokol** (§8) → **işlenmiş örnek** (§9) →
**tuzaklar ve doğrulama** (§10–11) → **maliyet** (§12).

Yeni bir kaynakla karşılaştığında doğrudan [§8](#8-grain-belirleme-protokolü--yeni-bir-kaynak-geldiğinde)'e
git; kavramları hatırlaman gerekirse §1–7'ye dön.

| # | Bölüm |
|---|---|
| [1](#1-grain-nedir) | Grain nedir, neden ilk karar |
| [2](#2-barış-önce-şöyle-sandı) | Barış önce şöyle sandı: OLTP ≠ OLAP |
| [3](#3-kümülatif-sayaç-tuzağı) | Kümülatif sayaç tuzağı |
| [4](#4-fact-table-türleri-kimball) | Fact table türleri (Kimball) |
| [5](#5-anahtar-seçimi) | Anahtar seçimi: natural/surrogate, NULL, URL |
| [6](#6-business-date-vs-technical-date) | Business date vs technical date |
| [7](#7-zaman-dilimi-graine-gün-giriyorsa-utc) | Zaman dilimi: neden UTC |
| [8](#8-grain-belirleme-protokolü--yeni-bir-kaynak-geldiğinde) | **Grain belirleme protokolü — 7 adım** |
| [9](#9-işlenmiş-örnek--bi-temporal-bir-kaynak) | **İşlenmiş örnek: hava durumu tahmini (bi-temporal)** |
| [10](#10-karışık-grain-mixed-grain-tuzağı) | Karışık grain, double counting, fan trap |
| [11](#11-grain-cümlesi-nasıl-test-edilir) | Grain cümlesi nasıl test edilir |
| [12](#12-grain-yanlışsa-maliyeti--ve-neden-geri-dönüş-asimetriktir) | Grain yanlışsa maliyeti, geri dönüş asimetrisi |

---

## 1. Grain nedir

**Grain = "bir satır neyi temsil ediyor" sorusunun cevabı.**

Tek cümleyle yazılamıyorsa grain belirlenmemiş demektir. Ve grain belirlenmeden yazılan
her transform kodu tahmindir.

Grain neden ilk karar:

| Karar | Grain'e nasıl bağlı |
|---|---|
| Birincil anahtar | Grain'in doğrudan ifadesi |
| Partition şeması | Genelde grain'deki zaman boyutu |
| Idempotency | "Aynı satır" tanımı grain'den gelir |
| Agregasyon | Grain'den yukarı toplanır, aşağı inilemez |

Son satır kritik: **grain'i sonradan inceltebilirsin, kalınlaştıramazsın.** Günlük veri
tutuyorsan aylık üretirsin; aylık tuttuysan günlüğü asla geri getiremezsin. Atılan detay
yok olmuştur. Bu asimetri, grain kararının kod yazılmadan **önce** alınmasının sebebi.

---

## 2. Barış önce şöyle sandı

**Sanılan:** "Bir satır = bir track. Aynı parça tekrar gelirse satırı güncellerim, en son
`playcount` kalır."

**Aslında:** Bu, tabloyu kaynak sistemin **bugünkü aynası** yapar. Uygulama veritabanı
(OLTP) böyle çalışır — orada geçmiş bir yüktür, güncel doğru tek şeydir.

Data warehouse'un (OLAP) işi tam tersi: **kaynak sistemi zaman içinde gözlemlemek.**

Bu ayrımı bir kere oturtmak, sonraki her modelleme kararını kolaylaştırıyor:

| | OLTP | OLAP / warehouse |
|---|---|---|
| Soru | "Şu an durum ne?" | "Zaman içinde ne oldu?" |
| Güncelleme | `UPDATE` normaldir | `UPDATE` bilgi kaybıdır |
| Geçmiş | Yük | Ürünün kendisi |

**Neden bu hata sessizdir:** üzerine yazan pipeline hiç hata vermez. Aylar sonra biri
"trend grafiği çıkaralım" der ve 90 günlük verinin hiç var olmadığı ortaya çıkar. Hiçbir
alarm çalmaz, çünkü teknik olarak her koşu başarılıydı. Veri mühendisliğindeki en pahalı
hatalar patlamaz, **sessizce eksik** çalışır.

---

## 3. Kümülatif sayaç tuzağı

Kaynak sistem sana bir sayaç veriyorsa (`playcount`, `view_count`, `total_downloads`) o
sayı **bir dönemin değeri değil, doğuştan bugüne toplamdır.**

Sonuç: **dönemsel değer türetilemez, ancak iki snapshot farkından hesaplanır.**

```
gunluk_calinma(t) = playcount(t) - playcount(t-1)
```

Snapshot'ı saklamazsan bu fark sonsuza kadar kaybolur. Sayaç değerinin kendisi bir gün
sonra hâlâ oradadır ama **aradaki hareket** yoktur.

Kontrol sorusu: bir alanın "dün 100, bugün 105" olması "dün 100 kere oldu" mu demek,
"toplam 105'e çıktı" mı? İkisi farklı model gerektirir.

---

## 4. Fact table türleri (Kimball)

Bu bir literatür sınıflandırması — Ralph Kimball, *The Data Warehouse Toolkit*. Uydurma
değil, mülakatta adıyla sorulur.

| Tür | Bir satır ne zaman doğar | Örnek |
|---|---|---|
| **Transaction** | Bir olay olduğunda | Satış, tıklama, scrobble |
| **Periodic snapshot** | Düzenli aralıklarla, olay olmasa bile | Günlük chart, ay sonu bakiye |
| **Accumulating snapshot** | Süreç başlarken, ilerledikçe **güncellenir** | Sipariş: verildi → ödendi → kargolandı |

Ayrım noktası: transaction fact'te satır bir **olayı**, periodic snapshot'ta bir
**durumu** temsil eder. Chart verisi olay değildir — "12 Ağustos'ta bu parça 3. sıradaydı"
bir durumdur, o gün hiçbir şey "olmasa" bile satır yazılır.

Accumulating snapshot tek istisnadır: orada `UPDATE` meşrudur, çünkü satırın kendisi bir
sürecin ömrünü temsil eder.

---

## 5. Anahtar seçimi

### Natural key vs surrogate key

| | Natural key | Surrogate key |
|---|---|---|
| Nedir | İş dünyasından gelen değer (`artist_name`, `isbn`, `email`) | Sistem üretir (`id`, hash, UUID) |
| Artısı | Okunabilir, kaynakla eşleşir, join için anlamlı | Değişmez, tek kolon, tipi sabit |
| Eksisi | Değişebilir, tipi kontrolünde değil | Anlamsız, kaynağa bağlamak için yine natural key gerekir |

Surrogate key "her sorunu çözer" değildir: onu bir şeyden **türetmen** gerekir, ve
türettiğin şey yine natural key'dir. Yani doğal anahtar sorunu ortadan kalkmaz, bir
katman aşağı iner.

### Yabancı sistemin anahtarını anahtar yapma

Kaynak sistemin sana verdiği her ID senin anahtarın değildir. Kritik ayrım: **o ID'yi kim
üretiyor?**

`mbid` örneği: MusicBrainz üretiyor, Last.fm sadece eşleştirebiliyorsa taşıyor. Üç sonucu
var:

1. Eşleşme yoksa alan **yok** — anahtarın parçası boş olamaz
2. Eşleşme sonradan kurulabilir — dün boş, bugün dolu → anahtar **değişti** → aynı varlık
   yeni kayıt gibi görünür
3. Eşleşme düzeltilebilir — yanlış mbid'in düzelmesi de anahtarı değiştirir

Kural: **anahtar, üzerinde kontrolün olmayan ve boş olabilen alandan kurulmaz.**
Böyle alanlar öznitelik olarak saklanır — değerlidir (dış sistemle join için), ama kimlik
değildir.

### Anahtara alan eklemek onu güçlendirmez

Junior sezgisi: "ne kadar çok kolon koyarsam o kadar garanti." Tersi doğru.

Anahtara alan eklemek **grain'i inceltir**. Yani aynı mantıksal varlığın iki satıra
bölünme ihtimalini artırır. `(a, b)` benzersizse `(a, b, c)` de benzersizdir — ama `c`
değişirse eskiden tek olan satır ikiye çıkar. Kazanç yok, risk var.

### NULL içeren anahtar SQL'de zorlanamaz

`UNIQUE` kısıtı `NULL != NULL` kuralıyla çalışır. Anahtarın bir bileşeni NULL olabiliyorsa
veritabanı benzersizliği **uygulayamaz** — iki özdeş satır sessizce girer. Bu, "NULL'lu
kolonu anahtara koyma" kuralının teorik değil mekanik sebebi.

### URL bir kimlik değil, adrestir

Kaynak sistemin URL'i benzersiz olabilir, ama URL sitenin **sunum katmanına** aittir.
Anahtar yaparsan veri modelin başkasının site yapısına bağlanır. Ayrıca encode'ludur:
her analitik filtre okunabilir bir eşitlik yerine kodlanmış string karşılaştırması olur.

Saklanır (kaynağın kanonik referansı), anahtar yapılmaz.

---

## 6. Business date vs technical date

En sık karıştırılan iki kolon:

| Kolon | Ne söyler | Ne zaman değişir |
|---|---|---|
| `snapshot_date` / `event_date` | Verinin **temsil ettiği** iş günü | Asla — o günün verisi hep o güne aittir |
| `ingested_at` / `loaded_at` | Verinin **işlendiği** an | Her yeniden işlemede |

Normal günlük koşuda ikisi çakışır ve "tek kolon yeter" gibi görünür. Ayrıldıkları an
**backfill**'dir: geçmiş bir günü bugün yeniden işlersen `ingested_at` bugündür,
`snapshot_date` geçmiştir. Tek kolon tutulmuşsa biri hakkında yalan söylemek zorundasın.

`ingested_at` gibi kolonlara **audit sütunu** ya da **lineage sütunu** denir: veriyi değil,
verinin nereden ve ne zaman geldiğini anlatırlar.

---

## 7. Zaman dilimi: grain'e "gün" giriyorsa UTC

Grain'de gün varsa, **kimin günü** sorusu cevaplanmak zorundadır.

Python'da tuzak nettir:

```python
date.today()          # local — makinenin saat dilimi
datetime.now(UTC)     # explicit
```

`date.today()` çalıştığı makinenin saatine bakar. Aynı pipeline ev makinesinde (TRT),
CI'da ve Lambda'da (UTC) koşuyorsa aynı veri farklı tarih alır — ve tarih anahtarın
parçasıysa **anahtar ortamdan ortama değişir**. Sonuç: aynı günün verisi iki satır olur
ya da idempotency kaybolur.

Kural: depolanan her zaman UTC'dir. Yerel saat yalnızca **sunum** katmanında üretilir.

Aynı tuzağın kardeşi: `datetime.utcnow()` (Python 3.12'den itibaren deprecated) timezone
bilgisi **taşımayan** bir nesne döndürür — yani UTC olduğunu bilmeyen bir UTC zamanı.
Doğrusu `datetime.now(timezone.utc)`.

---

## 8. Grain belirleme protokolü — yeni bir kaynak geldiğinde

Not 13 bir veri kaynağını **keşfetme** protokolü verir. Bu bölüm onun devamıdır: keşif
bitti, elinde gerçek payload var, şimdi grain kurulacak.

Prosedür şart, çünkü grain sezgiyle belirlendiğinde neredeyse her zaman **kaynağın bugünkü
hali** seçilir — en tanıdık görünen, en yanlış cevap.

Yedi adım, sırayla. Her adımın bir sorusu, bir çıktısı, bir tuzağı var.

---

### Adım 1 — Kaynağın doğasını sınıflandır

**Soru:** Kaynak sana *"ne oldu"* mu diyor, *"ne durumda"* mı?

Bu tek soru fact table türünü ve dolayısıyla grain'in iskeletini verir:

| Kaynak sana ne veriyor | Grain iskeleti | Tür |
|---|---|---|
| Olay listesi, her kayıtta kendi timestamp'i | 1 satır = 1 olay | Transaction |
| "Şu anki durum" sorgusu, tarih yok | 1 satır = 1 varlık × 1 gözlem anı | Periodic snapshot |
| Sürecin aşamaları, aynı kayıt güncelleniyor | 1 satır = 1 süreç örneği | Accumulating snapshot |
| Zaten toplanmış rapor / agregasyon | 1 satır = **kaynağın** seviyesi | — (seçim yok) |

**Tuzak:** son satır. Kaynak sana agrege veri veriyorsa grain'i sen seçmiyorsun, kaynak
seçmiş. "Daha detaylı isterim" diyemezsin — o detay hiç gelmedi. Bu durumda yapılacak tek
şey, sınırı **belgelemek**: tablonun asla cevaplayamayacağı soruları yazmak.

**Ayırt edici test:** aynı kaydı yarın tekrar sorsan aynı değeri döndürür mü? Döndürüyorsa
olaydır (geçmiş değişmez). Değişiyorsa durumdur — ve durum snapshot ister.

---

### Adım 2 — Zaman semantiğini bul

**Soru:** Veri kendi tarihini taşıyor mu?

| Cevap | Sonuç |
|---|---|
| Taşıyor (`created_at`, `played_at`, `event_time`) | Tarih veriden gelir, grain'in doğal parçasıdır |
| Taşımıyor | Tarihi **sen** ekliyorsun → kaynak sana bir durum verdi, olay değil |

İkinci satır kritik: **tarih alanının yokluğu bir eksiklik değil, bir bilgidir.** Kaynağın
sana bir zaman kesiti değil, "şu an" verdiğini söyler. Grain'e gözlem anını sen eklemek
zorundasın, ve o an artık anahtarın parçasıdır.

Burada üç ayrı zaman karışır, üçünü ayır (§6):

| Zaman | Nedir |
|---|---|
| Event time | Olayın gerçekte olduğu an |
| Observation / snapshot time | Senin gözlediğin an |
| Ingestion time | Senin işlediğin an |

Olay verisinde birinci ve üçüncü vardır; snapshot verisinde ikinci ve üçüncü.

**Tuzak:** kaynağın verdiği tarihi sorgusuz kabul etmek. `updated_at` bir event time
değildir — o alan geçmişe dönük değişir, yani anahtarda kullanılırsa anahtar da değişir.

---

### Adım 3 — Ölçümlerin (measure) doğasını sor

Fact tablodaki sayısal alanların **toplanabilirliği** grain'i doğrudan kısıtlar. Kimball
sınıflandırması:

| Tür | Zaman boyunca `SUM` anlamlı mı | Örnek |
|---|---|---|
| **Additive** | Evet | Satış tutarı, adet, süre |
| **Semi-additive** | Hayır — sadece son değer ya da fark anlamlı | Bakiye, stok, `playcount` gibi kümülatif sayaç |
| **Non-additive** | Hayır — hiçbir boyutta toplanamaz | Oran, yüzde, ortalama, sıralama (`rank`) |

**Semi-additive bir ölçüm gördüğün an snapshot tutmak zorunlu hale gelir.** Çünkü değerin
kendisi değil, **iki gözlem arasındaki fark** taşır bilgiyi. Üzerine yazarsan fark yok
olur (§3).

**Tuzak:** kümülatif sayacı additive sanmak. `SUM(playcount)` her zaman anlamsızdır ama
her zaman bir sayı döndürür — sessiz yanlış. Non-additive alanlarda da aynısı:
`AVG(rank)` çalışır, anlamı yoktur.

**Kontrol:** her sayısal alan için "bu alanı iki satır boyunca toplarsam anlamlı bir şey
elde eder miyim" diye sor. Cevap hayırsa alanın türünü şema tablosuna **yaz** — 5.8'deki
kalite kontrolleri buna dayanır.

---

### Adım 4 — En ince gözlemi al

**Soru:** Kaynağın verebildiği **en detaylı** satır nedir?

Grain oraya kurulur. İhtiyaca göre değil, kaynağın sınırına göre.

Gerekçe §1'deki asimetri: ince grain'den kalın üretilir (`GROUP BY`), tersi imkânsız.
Bugün kimse günlük detay istemiyor olabilir; altı ay sonra isteyen çıktığında veri ya
vardır ya yoktur.

**Tuzak — en yaygın anti-pattern:** grain'i **çıktıdan geriye doğru** belirlemek. Yani
"dashboard aylık gösterecek, aylık tutayım" demek. Yanlış, çünkü dashboard değişir, tablo
kalır. Sunum katmanı tabloya bakar; tablo sunuma bakmaz.

**Karşı-denge:** "en ince" sonsuz değildir. Kaynağın verdiğinden daha ince bir grain
uydurmak (var olmayan detayı türetmek) sahte kesinliktir. Sınır kaynağın verdiği yerdir.

---

### Adım 5 — Doğal anahtarı bul, sonra buda

**Soru:** Bu en ince gözlemi hangi alan kombinasyonu benzersiz kılıyor?

Adayı bulduktan sonra **her bileşeni tek tek sına**:

| Sınav | Kalırsa | Kalmazsa |
|---|---|---|
| Boş / eksik olabilir mi? | Anahtarda kalır | Öznitelik olur (§5, `NULL != NULL`) |
| Kim üretiyor — kaynak mı, üçüncü sistem mi? | Kaynak üretiyorsa kalır | Yabancı sistemin ID'si öznitelik olur |
| Zaman içinde değişebilir mi? | Değişmiyorsa kalır | Değişiyorsa kırılganlık **belgelenir** |

Sonra ters yönde bud: **anahtardan çıkarılabilecek her alanı çıkar.** Anahtara alan
eklemek onu güçlendirmez, grain'i inceltir ve çiftlenme riskini artırır (§5).

**Tuzak:** "her ihtimale karşı" anahtara alan eklemek. Bu bir tedbir değil, yeni bir hata
kaynağı.

---

### Adım 6 — Ölç, kabul etme

**Soru:** Aday anahtar gerçek veride **gerçekten** benzersiz mi?

Bu adım pazarlık konusu değil. Aday anahtar ne kadar mantıklı görünürse görünsün, kayıt
sayısı ile benzersiz kombinasyon sayısı **sayılarak** karşılaştırılır.

Ölçüm iki yönde de sonuç verir:

- Aday benzersiz değilse → grain yanlış, gözden kaçan bir boyut var
- İki aday **eşit** benzersizse → biri fazladan bilgi taşımıyor demektir, seçim
  mantıkla yapılır (Last.fm'de `url` böyle elendi)

**Tuzak — seçim yanlılığı:** ölçümü yalnızca verinin "güzel" kısmında yapmak. İlk sayfa,
son ay, popüler kayıtlar — bunlar veri kalitesinin en yüksek olduğu yerdir (not 13).
Anahtar ölçümü mutlaka **kuyrukta** da tekrarlanır. Last.fm'de `mbid`'in eksikliği yalnızca
son sayfada göründü.

---

### Adım 7 — Cümleyi kur, sonra tabloyu sorgula

Grain'i **tek cümleyle** yaz. Sonra tabloya üç gerçek soru sor — gelecekte birinin
soracağı türden, uydurma değil.

Örnek: "Bu parça hangi hafta zirveye çıktı?", "Dün kaç kez çalındı?", "Geçen ay chart'a
kaç yeni parça girdi?"

Bir soru cevaplanamıyorsa iki ihtimal var, ikisi de meşru:

| Durum | Ne yapılır |
|---|---|
| Grain yanlış | Grain düzeltilir — kod yazılmadan önce, bedava |
| Soru kapsam dışı | ADR'ye "bu tablo bunu cevaplamaz" diye **yazılır** |

İkincisini yazmak birincisi kadar değerlidir: kapsamı belgelenmemiş tablo, altı ay sonra
"neden çalışmıyor" diye suçlanır.

---

### Protokolün farklı kaynaklara uygulanması

Aynı yedi adım, dört farklı kaynak:

| Kaynak | Doğası (1) | Tarih taşıyor mu (2) | Ölçüm türü (3) | Grain |
|---|---|---|---|---|
| Ödeme sağlayıcı işlem API'si | Olay | Evet (`created_at`) | Additive (tutar) | 1 satır = 1 işlem |
| Last.fm chart | Durum | **Hayır** | Semi-additive (`playcount`) | 1 satır = 1 parça × 1 UTC gün |
| Banka hesap bakiyesi | Durum | Hayır | Semi-additive (bakiye) | 1 satır = 1 hesap × 1 gün sonu |
| Kargo sipariş takibi | Süreç | Kısmen (aşama tarihleri) | Additive + süre | 1 satır = 1 sipariş (güncellenir) |
| Google Analytics günlük rapor | Zaten agrege | Evet (rapor günü) | Karışık | 1 satır = kaynağın verdiği kırılım — **seçim yok** |
| Hava durumu tahmin API'si | Durum (gelecek hakkında) | Hedef zaman **var**, üretim zamanı **yok** | Çoğu non-additive | 1 satır = 1 şehir × 1 tahmin koşusu × 1 zaman dilimi → [§9](#9-işlenmiş-örnek--bi-temporal-bir-kaynak) |

Dikkat: ikinci ve üçüncü satır aynı yapıdadır. Farklı sektör, farklı API, aynı grain
kalıbı. Protokolün değeri burada — kalıbı tanıyorsan kaynağı tanımana gerek kalmıyor.

Son satır özellikle öğreticidir ve bir sonraki bölümde adım adım işlenmiştir.

---

## 9. İşlenmiş örnek — bi-temporal bir kaynak

Protokolü baştan sona, tek bir kaynak üzerinde çalıştıralım. Kaynak bilinçli olarak
Last.fm'den **farklı bir sınıftan** seçildi: orada tarih hiç yoktu, burada tarih **var** —
ve bu, seni yanlış güvene sokan daha kurnaz bir tuzak.

> Alan adları OpenWeather'ın 5 günlük / 3 saatlik forecast endpoint'ine dayanıyor ama
> **doğrulanmadı** — bu pedagojik bir örnek, ölçülmüş veri değil. Gerçek projede Adım 6'ya
> gelmeden bunlar sayılırdı.

Kaynak kabaca şunu döndürüyor (5 gün × günde 8 kayıt = 40 kayıt, 3 saatlik adımlar):

```json
{
  "city": { "id": 745044, "name": "Istanbul" },
  "list": [
    { "dt": 1755010800, "dt_txt": "2026-08-12 15:00:00",
      "main": { "temp": 31.2, "humidity": 44 },
      "pop": 0.12, "rain": { "3h": 0.0 }, "wind": { "speed": 4.1 } }
  ]
}
```

---

### Adım 1 — Kaynağın doğasını sınıflandır

İlk bakışta olay listesi gibi: her kaydın kendi `dt`'si var, düzgün sıralı. Junior refleksi
burada "1 satır = 1 saatlik ölçüm" demektir.

Ayırt edici testi uygula: **aynı kaydı yarın tekrar sorsan aynı değeri döndürür mü?**

Hayır. Yarın çağırdığında `dt = 1755010800` için `temp` 31.2 değil, 29.8 olacak. Çünkü bu
bir **ölçüm değil, tahmin** — olmuş bir şey değil, gelecek hakkında bir inanç. İnanç
değişir.

| | Sonuç |
|---|---|
| Sınıf | Durum (state), olay değil |
| Tür | Periodic snapshot |

**Yanlış cevap ne olurdu:** "1 satır = 1 saatlik tahmin" deseydin her çekim öncekini
ezerdi ve elinde sadece "en son ne düşündüğümüz" kalırdı.

---

### Adım 2 — Zaman semantiğini bul

Örneğin can alıcı yeri. **İki ayrı zaman ekseni var:**

| Zaman | Ne demek | Veride var mı |
|---|---|---|
| `dt` / `forecast_time` | Tahminin **hedeflediği** an (valid time) | **Var** |
| `issued_at` | Tahminin **üretildiği** an (transaction time) | **Yok** |

Last.fm'de tarih hiç yoktu ve eksiklik hemen görünüyordu. Burada tuzak daha ince: bir tarih
**var**, ve o tarih seni "zaman boyutu halloldu" diye rahatlatıyor. Ama var olan tarih
yanlış eksen — hedefi söylüyor, gözlem anını söylemiyor.

Buna **bi-temporal** veri denir: iki bağımsız zaman ekseni. Literatürde yerleşik bir
terimdir, benim adlandırmam değil.

Ek karar: `dt` UTC. İstanbul için "günlük ortalama" istenirse yerel güne göre gruplanır —
ama **depolama UTC kalır**, yerel gün sunum katmanında üretilir (bkz. §7).

**Dürüstlük notu:** senin ekleyeceğin `issued_at` aslında "biz çektik" anıdır, "model
koştu" anı değil. Aralarında gecikme var ve API bunu söylemiyor. Bu fark Adım 7'de
belgelenecek.

---

### Adım 3 — Ölçümlerin doğasını sor

| Alan | Tür | Neden |
|---|---|---|
| `temp` | Non-additive | `SUM(temp)` anlamsız; `AVG`/`MIN`/`MAX` anlamlı |
| `humidity` | Non-additive | Aynı |
| `pop` (yağış olasılığı) | Non-additive | Olasılık toplanmaz |
| `wind.speed` | Non-additive | Anlık hız |
| `rain.3h` (mm) | **Additive** | 3 saatlik pencerede **biriken** miktar |

Tek additive alan `rain.3h`, o da bir **pencere ölçümü**. Grain 3 saatlik olduğu sürece
toplanabilir — ama aynı pencere iki kez satıra girerse çift sayım olur (§10). Yani
`rain.3h`'in doğru toplanması tamamen anahtarın doğruluğuna bağlı.

Semi-additive alan **yok**, çünkü kümülatif sayaç yok. Last.fm'den yapısal fark budur.

**Tuzak:** `pop` ile `rain` aynı şey sanılır. Biri olasılık, diğeri miktar. `AVG(pop)` ile
`SUM(rain)` karıştırılırsa sorgu çalışır, sonuç saçmadır.

---

### Adım 4 — En ince gözlemi al

Kaynak **3 saatlik** veriyor. İhtiyaç "yarının günlük ortalama sıcaklığı" olsa bile grain
3 saatliktir. Gerekçe §1'deki asimetri: 3 saatlikten günlük üretilir, tersi imkânsız.

**Anti-pattern testi:** "dashboard günlük gösterecek, günlük tutayım" dersen, altı ay sonra
"gündüz–gece farkı nasıl?" sorusu geldiğinde elinde hiçbir şey olmaz. Veri hiç kaydedilmedi.

**Karşı-denge:** kaynak 3 saatlik veriyorsa saatlik grain uydurmak (interpolasyon) sahte
kesinliktir. Sınır kaynağın verdiği yerdir.

---

### Adım 5 — Doğal anahtarı bul, sonra buda

| Aday | Boş olabilir mi | Kim üretiyor | Değişir mi | Karar |
|---|---|---|---|---|
| `city.id` | Hayır | **Kaynağın kendisi** | Hayır | **Anahtarda** |
| `city.name` | Hayır | Kaynak | Evet, ve tekil değil (birden fazla "Springfield") | Öznitelik |
| `coord` (lat/lon) | Hayır | Kaynak | Float — eşitlik karşılaştırması kırılgan | Öznitelik |
| `dt` (forecast_time) | Hayır | Kaynak | Hayır | **Anahtarda** |
| `issued_at` | — | **Sen** | Hayır | **Anahtarda** |

Dikkat: **`city_id` kazandı, `mbid` kaybetmişti.** İkisi de "kaynağın verdiği ID" ama fark
belirleyici — `city_id` OpenWeather'ın *kendi* kimliği, `mbid` ise MusicBrainz'in yani
*üçüncü tarafın* kimliğiydi. Adım 5'in "kim üretiyor" sorusu tam bu ayrımı yakalamak için
var.

Bir karar daha: `issued_at`'in **çözünürlüğü** çekim sıklığına bağlıdır. Günde bir
çekiyorsan `issued_date` yeter; günde dört çekiyorsan tam timestamp gerekir, yoksa aynı
günün dört koşusu çakışır. Yani **çekim sıklığı anahtarın çözünürlüğünü belirler.**

---

### Adım 6 — Ölç, kabul etme

Tek payload üzerinde `(city_id, dt)` say: 40 kayıt, 40 benzersiz kombinasyon. Temiz
görünüyor — ve **seni yanıltır.**

Ertesi günün payload'ını da yükleyip birleştir:

| Ölçüm | Tek payload | İki payload birleşik |
|---|---|---|
| `(city_id, dt)` benzersiz mi | Evet | **Hayır** |
| `(city_id, issued_at, dt)` benzersiz mi | Evet | Evet |

İki koşu da aynı gelecek saatler için tahmin üretiyor, dolayısıyla `(city_id, dt)`
çakışıyor. `issued_at`'in gerekliliği tahminle değil **ölçümle** kanıtlanıyor.

Last.fm'de aynı dersin adı "ilk sayfa yalan söyledi" idi; burada "tek payload yalan
söylüyor". Kalıp aynı: **tek örnek üzerinde yapılan anahtar ölçümü yanıltıcıdır.**

---

### Adım 7 — Cümleyi kur, sonra tabloyu sorgula

| Soru | Cevaplanabilir mi |
|---|---|
| "Yarın İstanbul'da yağmur bekleniyor mu?" | Evet — en son `issued_at` |
| "Dün yaptığımız 3 günlük tahmin ne kadar tuttu?" | Yalnızca `issued_at` anahtardaysa |
| "Tahmin ufku uzadıkça hata artıyor mu?" | `forecast_time - issued_at` = **lead time**; ikisi de varsa |

İkinci ve üçüncü soru grain'i tek başına belirliyor. `issued_at`'i atarsan tablo yalnızca
birinci soruyu cevaplayabilen bir tabloya dönüşür — ve bunu fark etmen aylar sürer.

**Kapsam dışı olarak yazılacaklar** (Adım 7'nin ikinci maddesi):

- Bu tablo tahmin **doğruluğunu** tek başına ölçemez. Gerçekleşen değerler (actuals) ayrı
  bir kaynaktan gelir, ayrı tabloda durur; doğruluk join ile hesaplanır.
- `issued_at` model koşu anı değil, çekim anıdır. Aradaki gecikme bilinmiyor ve bu
  tablodan çıkarılamaz.

---

### Sonuç

> **Bir satır = bir şehir için, belirli bir çekim anında üretilmiş, belirli bir 3 saatlik
> gelecek zaman dilimine ait tahmin.**

**Birincil anahtar:** `(city_id, issued_at, forecast_time)`

Tür: periodic snapshot'ın bi-temporal varyantı — düzenli aralıklarla yazılır, satır asla
güncellenmez.

---

### İki örneğin karşılaştırması

| | Last.fm chart | Hava tahmini |
|---|---|---|
| Kaynak doğası | Durum | Gelecek hakkında durum |
| Veride tarih | **Hiç yok** | Hedef zaman var, üretim zamanı yok |
| Zaman ekseni | 1 (`snapshot_date`) | 2 (`issued_at` + `forecast_time`) |
| Ölçüm türü | Semi-additive (kümülatif sayaç) | Çoğu non-additive, biri additive pencere |
| Kaynak ID'si | Elendi — üçüncü tarafın (`mbid`) | Kazandı — kaynağın kendi (`city_id`) |
| Ölçümün açığa çıkardığı | Kuyrukta eksik alan | İki payload birleşince çakışan anahtar |

Aynı yedi adım, farklı sonuçlar. Protokolün işi cevabı vermek değil — **hangi sorunun
sorulacağını garanti etmek.**

---

## 10. Karışık grain (mixed grain) tuzağı

Tek tabloda **iki farklı grain'e ait** ölçüm bulundurmak, bu konudaki en pahalı ikinci
hatadır.

Klasik örnek: sipariş satırları tablosu.

| order_id | line_id | line_amount | shipping_fee |
|---|---|---|---|
| 1001 | 1 | 50 | **10** |
| 1001 | 2 | 30 | **10** |
| 1001 | 3 | 20 | **10** |

`line_amount` satır seviyesinde, `shipping_fee` **sipariş** seviyesinde. Tablonun grain'i
satır olduğu için kargo ücreti üç kez tekrarlanmış.

Sonuç: `SUM(shipping_fee)` = 30, gerçek değer 10. Sorgu hata vermez, üç katı bir sayı
döndürür. Buna **double counting** denir; join üzerinden oluşan hâline **fan trap** denir.

Çözüm iki tanedir:

1. Farklı grain'deki ölçümü **ayrı tabloya** koy (sipariş başlığı ayrı, satırlar ayrı)
2. Zorunluysa **oransal dağıt** (allocation) ve bunu kolon adında belirt:
   `shipping_fee_allocated`

**Kontrol sorusu:** tablodaki her sayısal alan için "bu değer grain'in tanımladığı satır
için mi ölçüldü, yoksa daha kalın bir şey için mi" diye sor. Cevap ikinci ise alan yanlış
tablodadır.

---

## 11. Grain cümlesi nasıl test edilir

Protokolü uyguladın, cümleyi kurdun. Sağlam mı? Dört soru:

1. **Tek cümle mi?** "ve" içeriyorsa muhtemelen iki tablodur.
2. **İki kere çalıştırınca ne olur?** Aynı girdi aynı anahtarı üretiyor mu?
3. **Anahtarın hiçbir bileşeni boş olabiliyor mu?** Olabiliyorsa anahtar değildir.
4. **Yarın kaynak değişirse hangi bileşen kayar?** Cevabı bilmiyorsan kırılganlığı da
   bilmiyorsun.

Dördüncüsü ADR'nin "Consequences" bölümünü doldurur: sadece iyi tarafı yazılmış bir karar,
karar değil savunmadır.

---

## 12. Grain yanlışsa maliyeti — ve neden geri dönüş asimetriktir

Yanlış grain'in diğer hatalardan farkı **ne zaman fark edildiğidir**:

| Hata türü | Ne zaman anlaşılır | Düzeltme maliyeti |
|---|---|---|
| Syntax hatası | Saniyeler içinde | Sıfır |
| Bozuk transform mantığı | Testte ya da ilk koşuda | Düşük — raw'dan yeniden üret |
| Yanlış tip / null davranışı | Haftalar içinde, bir sorgu tuhaf sonuç verince | Orta — geçmiş yeniden işlenir |
| **Yanlış grain** | **Aylar sonra, cevaplanamayan bir soruyla** | **Veri kaybettiyse sonsuz** |

Son satırın "sonsuz" olmasının sebebi:

| Değişim yönü | Mümkün mü |
|---|---|
| Grain'i inceltmek (detay eklemek) | Yalnızca kaynak veriyi hâlâ tutuyorsan |
| Grain'i kalınlaştırmak (agrege etmek) | Her zaman — `GROUP BY` yeter |
| Atılmış gözlemi geri getirmek | **Hayır** |

**Raw katman tam olarak bu asimetriyi hafifletmek için vardır.** Ham cevabı dokunmadan
sakladığın sürece, curated tabloyu farklı bir grain ile **yeniden üretebilirsin** — ama
yalnızca gerçekten çektiğin günler için. Raw katman grain hatasını ucuzlatır, ortadan
kaldırmaz.

**Pratik sonuç — üç kural:**

1. Grain kararı **kod yazılmadan önce** alınır. Sonrası pahalıdır.
2. Grain kararı **ADR'ye yazılır**, çünkü koda bakarak geri çıkarılamaz — kodda görünen
   sadece sonuçtur, alternatifler ve gerekçe değil.
3. Emin değilsen **daha ince** olanı seç. İnce grain depolama maliyetidir; kalın grain
   bilgi kaybıdır. İkisi aynı ağırlıkta değildir.

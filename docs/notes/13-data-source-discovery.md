# 13 — Yeni bir veri kaynağını keşfetmek: protokol

> Adım 1.5 · 2026-08-11

Bu not, **herhangi bir** yeni veri kaynağıyla (REST API, veritabanı tablosu, CSV dump,
Kafka topic) karşılaştığında sırayla uygulanacak bir protokoldür. Last.fm'e özgü değil —
Last.fm yalnızca örnek.

Amaç: "veriye baktım, tamam görünüyor" cümlesini yasaklamak. Bakmak ölçmek değildir.

---

## Neden bir protokol gerekiyor

Şema tasarımı, gördüğün veriye göre yapılır. Ama **gördüğün veri, verinin kendisi
değildir** — bir örneklemdir. Ve örneklem neredeyse hiçbir zaman rastgele değildir.

Bu projede yaşanan somut örnek:

| Ölçüm | İlk 20 kayıt | Son sayfadaki 19 kayıt |
|---|---|---|
| Boş `mbid` | 0 | 4 (%21) |
| `duration == 0` | 0 | 2 |
| Tüm kayıtlar aynı alanlara sahip | Evet | **Hayır** |

İlk 20 kayıt "veri tertemiz" dedi. İkisi de aynı endpoint, aynı gün, aynı parametreler —
tek fark `page` numarasıydı.

Sebep: chart popülerlik sırasına göre dönüyor. En popüler kayıtlar aynı zamanda **en iyi
kürate edilmiş** kayıtlardır. İlk sayfa, veri kalitesinin en yüksek olduğu yerdir.

Bunun adı **seçim yanlılığıdır** (selection bias). Junior'ın klasik cümlesi:
*"test verimde null yoktu, demek ki bu alan null gelmiyor."*

---

## Protokol: altı boyut

Her kaynakta bu altı soru sorulur. Sırayla.

### 1. Yapı — veri nerede

| Soru | Neden |
|---|---|
| En üstte hangi anahtar var? | Sarmalayıcı (envelope) mı, doğrudan veri mi |
| Kaç katman iç içe? | Düzleştirme işinin büyüklüğü |
| Metadata nerede, veri nerede? | Sayfalama bilgisi veriyle karışmamalı |

```python
print(list(d.keys()))
print(list(d["tracks"].keys()))
print(list(kayitlar[0].keys()))
```

### 2. Kapsam — bana ne kadarı geldi

En çok atlanan boyut budur.

| Soru | Neden kritik |
|---|---|
| Toplam kaç kayıt var? | `total` alanı var mı, doğru mu |
| Bana kaç tanesi geldi? | Varsayılan `limit` nedir |
| **Hangi sırayla geldi?** | Sıra rastgele değilse örneklem yanlıdır |
| Baştan, ortadan ve **sondan** örneklem aldım mı? | Kalite genelde kuyrukta düşer |

> **Kural: en az iki farklı yerden örneklem al.** Baş ve son. Aralarındaki fark,
> verinin gerçek dağılımı hakkında tek örneklemden fazlasını söyler.

Bu projede: `page=1` ve `page=500`. Fark dramatikti.

Sıralama bilgisi yoksa (`ORDER BY` yok, API sıra garantisi vermiyor) bu ayrı bir risktir —
sayfalama sırasında kayıt kaçırabilir ya da iki kez okuyabilirsin.

### 3. Alanlar — her kayıtta aynı mı

```python
setler = {tuple(sorted(x.keys())) for x in kayitlar}
print("alan setleri ayni:", len(setler) == 1)
print(setler)
```

`False` çıkarsa şema "her kayıtta şu alanlar var" diyemez. JSON şemasız bir formattır;
API bir alanı sessizce atlayabilir.

**Bu, üç farklı kod davranışı demektir:**

```python
x["mbid"]           # anahtar yoksa KeyError
x.get("mbid")       # None doner
x.get("mbid", "")   # "" doner
```

İlk sayfada `x["mbid"]` çalışır, kuyrukta patlar. Fark, testin hangi veriyle yapıldığında
gizlidir.

### 4. Tipler — beyan edilen ile gerçek

| Soru | Tipik bulgu |
|---|---|
| Sayılar gerçekten sayı mı? | XML kökenli API'lerde **hepsi string** |
| Tarihler hangi formatta? | Unix timestamp mi, ISO 8601 mi, yerel saat mi |
| Boolean nasıl geliyor? | `true` / `"1"` / `"yes"` / `1` |
| Aynı alan her kayıtta aynı tipte mi? | Bazen `"0"`, bazen `0`, bazen `{...}` |

```python
print({type(x.get("duration")).__name__ for x in kayitlar})
```

Son satır önemli: bir alanın **kayıttan kayda tip değiştirmesi** gerçek bir olaydır ve
Pydantic olmadan sessizce geçer.

### 5. Null'ın kaç yüzü var

Bu boyut en çok hata üreten yerdir. "Eksik veri" tek bir şey değildir:

| Biçim | Örnek | `is None` yakalar mı | `not x` yakalar mı |
|---|---|---|---|
| Gerçek null | `None` | Evet | Evet |
| Boş string | `""` | **Hayır** | Evet |
| Sıfır | `0`, `"0"` | Hayır | `0` evet, `"0"` **hayır** |
| Anahtarın hiç olmaması | — | **KeyError** | — |
| Placeholder metin | `"N/A"`, `"unknown"`, `"-"` | Hayır | **Hayır** |
| Varsayılan içerik | Herkese aynı gelen resim URL'si | Hayır | **Hayır** |

Son iki satır en sinsi olanıdır: **dolu görünen boş veri.**

Bu projede iki örneği birden çıktı:

- `duration: "0"` — parça 0 saniye mi sürüyor, yoksa süre bilinmiyor mu? İkisi farklı
  şey ve API ayırt etmiyor. Ortalama süre hesaplarsan `0`'lar sonucu bozar.
- `image` — 20 parça × 4 boyut = 80 URL bekleniyordu, **4 benzersiz URL** çıktı. Hepsi
  Last.fm'in "resim yok" varsayılanı. Alan dolu, içerik yok.

```python
# Alan gercekten bilgi tasiyor mu: benzersiz deger sayisi kayit sayisina yakin mi
degerler = {x["alan"] for x in kayitlar}
print(len(degerler), "benzersiz /", len(kayitlar), "kayit")
```

Benzersiz değer sayısı 1 ise o alan hiçbir bilgi taşımıyordur — sabit bir sütundur.

### 6. Tekillik ve sınırlar

| Soru | Neden |
|---|---|
| Bir satır neyi temsil ediyor? | Grain kararı — tüm transform buna dayanır |
| Hangi alan tekil? Gerçekten tekil mi? | Doğal anahtar adayı |
| Anahtar adayı **her kayıtta dolu mu**? | Boşsa anahtar değildir |
| Rate limit ne? | Retry ve backoff stratejisi |
| Sayfalama tavanı var mı? | `total` gerçek mi, tavan mı |

```python
print("kayit :", len(kayitlar))
print("tekil :", len({x.get("mbid") for x in kayitlar}))
```

İki sayı eşit değilse ya tekrar var ya da anahtar boş geliyor.

Bu projede `total: 10000` ve `totalPages: 500` çıktı — `500 × 20 = 10000` tam sayısı,
gerçek bir sayım değil **tavan** olduğunu düşündürüyor. Son sayfa ayrıca 20 değil
**19** kayıt döndürdü, yani `total` zaten tutarsız.

---

## Örnekleme stratejisi

Tek bir örneklem yeterli değildir. Minimum:

| Örneklem | Ne yakalar |
|---|---|
| İlk sayfa | Mutlu yol, en temiz kayıtlar |
| **Son sayfa** | Kalitenin en düşük olduğu yer |
| Rastgele bir orta sayfa | Genel dağılım |
| Sonuç dönmeyen bir sorgu | Boş cevabın **şekli** — hata mı, boş liste mi |
| Hatalı parametre | Hata cevabının şekli |

Son iki satır çoğu zaman atlanır. Boş sonucun nasıl geldiğini bilmiyorsan, sıfır satırlı
bir günü hatadan ayırt edemezsin — sessiz veri kaybının kaynağı budur.

---

## Dört kod kalıbı

Bu notta geçen bütün ölçümler şu dörtten türedi:

```python
len(kayitlar)                                  # kac kayit
sum(1 for x in kayitlar if <kosul>)            # kac tanesi soyle
{tuple(sorted(x.keys())) for x in kayitlar}    # kac farkli alan seti
{x.get("alan") for x in kayitlar}              # kac farkli deger
```

Zor olan kod değil, **hangi soruyu soracağını bilmek**. Kod dört satır; soru listesi
yukarıdaki altı boyut.

### Ölçeklendiğinde: pandas

Birkaç yüz kaydı geçince elle saymak yorucu olur:

```python
import pandas as pd
df = pd.json_normalize(kayitlar)   # ic ice yapiyi duzlestirir

df.info()          # sutunlar, non-null sayilari, tipler
df.describe()      # sayisal ozet
df.isna().sum()    # sutun basina eksik sayisi
df.nunique()       # sutun basina benzersiz deger sayisi
df.duplicated().sum()
```

`df.nunique()` §5'teki "dolu görünen boş alan" testinin hazır hâlidir: bir sütunun
benzersiz değer sayısı 1 ise o sütun bilgi taşımıyordur.

**Uyarı:** `isna()` yalnızca gerçek `None`/`NaN` sayar. `""`, `"0"`, `"N/A"` ve
placeholder içerik **eksik sayılmaz**. Otomatik profil çıkaran araçlar (ydata-profiling
gibi) da aynı sınıra takılır. Dolu görünen boş veriyi hâlâ insan bulur.

---

## Kontrol listesi — kes ve sakla

Yeni bir kaynağa bakarken sırayla:

- [ ] En üst yapı: sarmalayıcı var mı, veri hangi anahtarda
- [ ] Metadata var mı (`total`, `page`, `hasMore`) — ve **güvenilir mi**
- [ ] Kaç kayıt geldi, varsayılan `limit` ne
- [ ] Veri **hangi sırayla** geliyor
- [ ] **En az iki farklı sayfadan** örneklem alındı mı (baş + son)
- [ ] Tüm kayıtlar aynı alan setine sahip mi
- [ ] Her alanın tipi ne — sayılar gerçekten sayı mı
- [ ] Bir alan kayıttan kayda tip değiştiriyor mu
- [ ] Eksik veri hangi biçimde geliyor: `null` / `""` / `0` / anahtar yok / placeholder
- [ ] Her alan için: benzersiz değer sayısı kaç (1 ise bilgi taşımıyor)
- [ ] Doğal anahtar adayı var mı, **her kayıtta dolu mu**
- [ ] Tekrar eden kayıt var mı
- [ ] Boş sonucun şekli ne (hata mı, boş liste mi)
- [ ] Hata cevabının şekli ne
- [ ] Rate limit ve sayfalama tavanı
- [ ] Bulgular yazıldı mı — payload diske kaydedildi mi

---

## Barış önce şöyle sandı

| Sandığım | Gerçek |
|---|---|
| Bu testler API'ye özel, başka yerde aklıma gelmez | Altı boyut kaynak-bağımsız. Değişen tek şey komutun sözdizimi (SQL, pandas, curl) |
| Bu kodu yazmak zor | Dört kalıp: `len`, `sum(1 for ...)`, `{tuple(sorted(...))}`, `{x[alan] for ...}` |
| İlk 20 kayıt temizse veri temizdir | İlk 20, popülerlik sırasında en iyi kürate edilmiş 20'dir. Kuyrukta %21 boş `mbid` çıktı |
| Alan ya vardır ya `null`'dur | Anahtarın **hiç olmaması** üçüncü bir durum ve `KeyError` üretir |
| `image` alanı dolu, sorun yok | 80 URL yerine 4 benzersiz URL — hepsi varsayılan resim. Dolu görünen boş veri |

---

## Mülakat

**"Yeni bir veri kaynağıyla çalışmaya nasıl başlarsın?"**
→ *"Şema yazmadan önce ölçerim. Yapı, kapsam, alan tutarlılığı, tipler, eksik verinin
biçimleri, tekillik ve sınırlar. En önemlisi birden fazla yerden örneklem almak —
ilk sayfa neredeyse her zaman verinin en temiz kısmıdır ve tek başına yanıltır."*

**"Veri kalitesi kontrolü derken neyi kastediyorsun?"**
→ *"Null oranı, satır sayısı ve tekillik en temel üçü. Ama asıl zor olan 'dolu görünen
boş veri' — placeholder metinler, herkese aynı gelen varsayılan değerler, anlamı
belirsiz sıfırlar. Bunları `isna()` yakalamaz; benzersiz değer sayısına bakmak gerekir."*

**"Bir alanın null gelmediğinden nasıl emin olursun?"**
→ *"Emin olamam, sadece ölçebilirim — ve ölçtüğüm örneklemin nasıl seçildiğini bilmem
gerekir. Sıralı bir kaynakta baştan alınan örneklem yanlıdır. Kod tarafında ise emin
olmaya çalışmam: şema doğrulamasını kodun kendisine koyarım ki varsayım kırıldığında
sessizce geçmesin."*

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **selection bias** | Örneklemin rastgele olmaması; sıralı veride ilk N kayıt tipik değildir |
| **natural key** | Verinin kendisinden gelen benzersiz tanımlayıcı (`mbid` gibi), üretilmiş ID'nin aksine |
| **grain** | Bir satırın neyi temsil ettiği. Tüm transform mantığının dayanağı |
| **envelope** | Asıl veriyi saran dış yapı (`{"tracks": {"track": [...]}}`) |
| **placeholder** | Eksik veri yerine konan sahte içerik ("N/A", varsayılan resim) |
| **cardinality** | Bir alanın kaç farklı değer aldığı. 1 ise bilgi taşımaz |
| **profiling** | Veri setinin istatistiksel özetini otomatik çıkarma |

# 16 — Shell'de döngü ve ölçüm: `for`/`while`, `curl -w`, gecikme istatistikleri

> **Bu notun sorusu:** *Shell'den tekrarlı bir iş nasıl yapılır ve bir şey nasıl ölçülür?*
>
> **Not 11'in sorusu** farklı: *bir API'yi elle nasıl çağırırım, auth nasıl çalışır?*
> **Not 12'nin sorusu** da farklı: *shell'in temel yapıları nasıl çalışır?*
>
> Üçünde de `curl` geçiyor. Ama **bir notun sınırını kullandığı araç değil, cevapladığı
> soru çizer.** Testi basit: buradaki bilgi `curl` olmadan da geçerli mi? Evet — döngü
> seçimi ve ölçüm disiplini her komuta uygulanır. Öyleyse ayrı not.
>
> Aynı test dosya/modül sınırı çizerken de kullanılır: *"bu dosyanın sorumluluğu nerede
> bitiyor"* sorusunun cevabı, içindeki kütüphane değil, cevapladığı sorudur.

**İlgili:** döngü dışı shell temelleri → [not 12](12-shell-basics.md) ·
`curl` bayrak kataloğu → [not 11 §5](11-manual-api-calls-and-auth-models.md)

> **Kısa cevap** — Shell'den tekrarlı iş nasıl yapılır ve bir gecikme dürüstçe nasıl ölçülür?
>
> 1. `{1..$N}` çalışmaz: brace expansion, değişken genişletmesinden önceki geçişte biter.
> 2. curl döngüsü her turda TCP+TLS'i yeniden öder; Python istemciden istek başına 50-150 ms yüksek ölçer.
> 3. Dış API'ye istek atan döngüde üst sınır garanti, koşul sadece fırsattır; 20 örnekle p95 istatistik değil gürültüdür.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

---

## 1. Döngü formları

### `for` — tekrar sayısı önceden belli

```bash
for i in {1..20}; do
  echo "request $i"
done
```

**Tuzak — `{1..$N}` çalışmaz.**

```bash
N=20
for i in {1..$N}; do echo "$i"; done   # prints the literal string {1..20}
```

Sebep: brace expansion, shell'in **en erken** yaptığı işlemlerden biri; değişken
genişletmesinden **önce** çalışır. Yani `$N` daha değerini almadan brace expansion bitmiştir.
Bu, "shell komutu soldan sağa okur" sezgisinin yanlış olduğu yerlerden biri — shell bir
satırı **birden fazla geçişte** işler ve geçişlerin sırası sabittir.

Değişkenli iki doğru form:

```bash
for i in $(seq 1 "$N"); do ... done      # portable, works in sh too
for ((i = 1; i <= N; i++)); do ... done  # bash-only, no subprocess, preferred in bash
```

İkincisi bir alt süreç açmaz (`seq` ayrı bir programdır), döngü sayısı büyükse fark eder.

Liste ve glob üzerinde:

```bash
for name in success edge_cases; do ... done
for f in tests/fixtures/lastfm/*.json; do ... done
```

**Glob tuzağı:** hiçbir dosya eşleşmezse bash varsayılan olarak deseni **literal string**
olarak verir — döngü bir kere, `*.json` metniyle çalışır. `shopt -s nullglob` bunu kapatır
(eşleşme yoksa döngü hiç dönmez). Script yazarken neredeyse her zaman istenen davranış budur.

### `while` — bitiş koşulu duruma bağlı

```bash
i=1
while [ "$i" -le 20 ]; do
  i=$((i + 1))
done
```

En yaygın ve en değerli kullanımı satır satır okuma:

```bash
while read -r line; do
  echo "$line"
done < measurements.csv
```

**`-r` neden her zaman?** `-r` olmadan `read`, ters bölü işaretini (`\`) kaçış karakteri
sayar ve veriyi sessizce bozar. Windows yollarında (`C:\Users\...`) bu doğrudan veri kaybıdır.
`read` neredeyse her zaman `-r` ile yazılır; `-r`'siz `read` görürsen çoğu zaman bir hatadır.

### `until` — koşul sağlanana kadar

Nadiren kullanılır; `while` + `!` genelde daha okunur. Bilmek yeter.

### Hangi formu seçmeli

| Durum | Form |
|---|---|
| Tekrar sayısı önceden belli | `for` |
| Bir liste / glob / komut çıktısı üzerinde | `for` |
| Satır satır dosya veya akış okuma | `while read -r` |
| Bitiş koşulu duruma bağlı (retry, polling) | `while` |
| Sonsuz + içeriden çıkış | `while true` + `break` |

### 1.8 için doğru form ve gerekçesi

Rate limit ölçümünde iki koşul var: **en fazla 20 istek** ve **error 29 görülürse dur.**
Doğru form `for` + `break`:

```bash
for i in $(seq 1 20); do
  # ... make request, read body ...
  if [ "$api_error" = "29" ]; then
    echo "rate limited at request $i"
    break
  fi
done
```

Neden `while` değil? Çünkü:

> Üst sınır bir **garantidir**, koşul bir **fırsattır**.

`for` üst sınırı dilin kendisine yaptırır. `while` kullanırsan sınırı elle bir sayaçla
korumak zorundasın — ve o sayacı unutmak veya yanlış artırmak **sonsuz döngü** demektir.

Bu ölçümde sonsuz döngünün bedeli sıradan değil: **üçüncü tarafa ait bir API'ye sonsuz
istek** demektir. Yani API key'in banlanır (hata kodu 26). Kontrol akışı seçimi burada bir
stil tercihi değil, bir emniyet kararıdır.

**Genel kural:** dış dünyaya istek atan hiçbir döngü, üst sınırı garanti altında olmadan
yazılmaz. Retry döngüleri de aynı: `max_attempts` daima vardır.

### `break` ve `continue`

| | Ne yapar |
|---|---|
| `break` | Döngüden **tamamen** çıkar |
| `continue` | Bu turu atlar, sonrakine geçer |
| `break 2` | İç içe döngüde **iki** seviye birden çıkar |

### Paralel döngü — ve burada neden yasak

```bash
# DO NOT run this against a third-party API you do not own.
seq 1 20 | xargs -P 8 -I{} curl -s "$URL"
```

`xargs -P 8` sekiz isteği aynı anda gönderir; GNU `parallel` daha da yetenekli. İkisi de
gerçek araçlar — ama rate limit **ölçerken** kullanılmaz, çünkü ölçmeye çalıştığın sınırı
kontrolsüz biçimde aşarlar. Paralellik, limit bilindikten **sonra** ve limitin altında
kalacak şekilde tasarlanır (adım 3.6).

---

## 2. PowerShell karşılıkları

```powershell
foreach ($i in 1..20) { ... }              # statement form
1..20 | ForEach-Object { ... }             # pipeline form, $_ = current item
while ($i -le 20) { ... }
```

**Kritik tuzak — `ForEach-Object` içinde `break` çalışmaz.**

| Yapı | `break` davranışı |
|---|---|
| `foreach (...) { }` | Döngüden çıkar — **beklenen davranış** |
| `... \| ForEach-Object { }` | Bu bir döngü değil, **pipeline cmdlet'i**. `break` içeren komut bloğu, kendisini saran döngüden çıkmaya çalışır; döngü yoksa davranış şaşırtıcıdır. |
| `... \| ForEach-Object { return }` | `return` yalnızca **o turu** bitirir — `continue` gibi davranır, `break` gibi değil |

Erken çıkış gerekiyorsa `foreach` kullan. 1.8'de erken çıkış gerekiyor, dolayısıyla
PowerShell tarafında doğru form `foreach`.

> **Genel ders:** PowerShell'de "döngü gibi görünen" iki ayrı şey var — dil seviyesindeki
> döngü ifadeleri ve pipeline cmdlet'leri. Akış kontrolü (`break`/`continue`) yalnızca
> birincisinde beklendiği gibi çalışır. bash'te böyle bir ayrım yok, alışkanlık yanıltır.

Süre ölçmek için:

```powershell
$elapsed = Measure-Command { curl.exe -s $url }
$elapsed.TotalMilliseconds
```

`curl.exe` — `.exe` şart, çünkü PowerShell'de `curl` bir alias'tır (not 11 §6).

---

## 3. `curl -w` — ölçüm bayrağı

`-w` (`--write-out`), istek bittikten **sonra** curl'ün kendi ölçtüğü değerleri yazdırır.
Gövdeden bağımsızdır, ek maliyeti yoktur.

| Değişken | Ne ölçer |
|---|---|
| `%{http_code}` | HTTP durum kodu |
| `%{time_namelookup}` | DNS çözümlemesi bitene kadar |
| `%{time_connect}` | TCP el sıkışması bitene kadar |
| `%{time_appconnect}` | **TLS** el sıkışması bitene kadar |
| `%{time_starttransfer}` | **İlk bayt gelene kadar (TTFB)** — sunucunun düşünme süresi |
| `%{time_total}` | İstek tamamen bitene kadar |
| `%{size_download}` | İndirilen gövde boyutu (bayt) |
| `%{num_redirects}` | Takip edilen yönlendirme sayısı |
| `%{url_effective}` | Yönlendirmelerden sonra ulaşılan URL |
| `%{exitcode}` / `%{errormsg}` | curl'ün kendi hatası (7.75+) |

Bu değerler **kümülatiftir**, birbirinin üzerine biner:

```
time_namelookup  <  time_connect  <  time_appconnect  <  time_starttransfer  <  time_total
       DNS              TCP              TLS                  TTFB                indirme
```

Yani "sunucu ne kadar düşündü" sorusunun cevabı `time_total` değil,
`time_starttransfer - time_connect`'tir. Rate limit ölçümünde ilgilendiğin şey budur —
`time_total` küçük bir JSON'da ona yakındır ama aynı şey değildir.

**`\n` unutulmaz:** `-w` çıktısına satır sonu koymazsan tüm ölçümler tek satırda birleşir.

```bash
curl -s -o /dev/null -w "%{http_code} %{time_starttransfer} %{time_total}\n" "$URL"
```

Okunabilir çıktı için format dosyası — profesyonel kalıp:

```bash
# curl-format.txt
dns:      %{time_namelookup}s
tcp:      %{time_connect}s
tls:      %{time_appconnect}s
ttfb:     %{time_starttransfer}s
total:    %{time_total}s
```

```bash
curl -s -o /dev/null -w "@curl-format.txt" "$URL"
```

### En önemli ölçüm tuzağı: bağlantı yeniden kullanımı

Döngüdeki **her `curl` çağrısı ayrı bir süreçtir** ve sıfırdan TCP + TLS el sıkışması yapar.
Gerçek bir istemci (`requests.Session`, `httpx.Client`, `aiohttp`) bağlantıyı açık tutar ve
ikinci istekten itibaren bu maliyeti **ödemez**.

Somut sonucu:

> `curl` döngüsüyle ölçtüğün gecikme, Python istemcinin göreceğinden **sistematik olarak
> yüksektir** — tipik olarak istek başına 50–150 ms fazla.

Bunu `time_appconnect` ile doğrularsın: her turda sıfırdan büyükse TLS her seferinde
yeniden kuruluyor demektir.

**Bu hatanın adı var: ölçüm aracı ölçülen şeyi temsil etmiyor.** Ölçtüğün "Last.fm ne kadar
yavaş" değil, "curl'ü 20 kere başlatmak ne kadar sürüyor". Genel bir tuzak sınıfıdır:
yerel diski ölçerken önbelleği unutmak, sorgu süresini ölçerken bağlantı kurulumunu saymak,
fonksiyonu ölçerken JIT ısınmasını saymak — hepsi aynı hata.

**Nasıl kaçınılır:**

| Yöntem | Nasıl |
|---|---|
| Tek `curl` çağrısına birden fazla URL ver | curl aynı host'a bağlantıyı yeniden kullanır |
| Ölçümü Python'da yap | `httpx.Client()` ile — gerçek istemciyi ölçmüş olursun |
| En azından **kabul et ve yaz** | Ölçümün yanına "TLS her turda yeniden kuruldu" notu düş |

Üçüncüsü en az yapılan ama en önemli olanıdır: **ölçümün bilinen yanlılığını ölçümle
birlikte kaydet.** Yanlılığı olmayan ölçüm yoktur; belgelenmemiş yanlılık vardır.

---

## 4. Çıktı kontrolü: gövdeyi ve ölçümü birlikte almak

| Bayrak | Ne yapar | Ölçümde rolü |
|---|---|---|
| `-s` | Progress metresini susturur | **Şart.** Progress metresi stderr'e gider ve çıktıyı kirletir |
| `-S` | `-s` ile birlikte gerçek hataları gösterir | `-sS` ikilisi standarttır |
| `-o dosya` | Gövdeyi dosyaya yazar | Gövde lazımsa |
| `-o /dev/null` | Gövdeyi atar | Sadece ölçüm lazımsa |
| `-D -` | Header'ları stdout'a akıtır | `x-ratelimit-*` aramak için |
| `--max-time N` | Toplam süre tavanı | **Ölçüm döngüsünde şart** — asılı bir istek döngüyü kilitler |

**Hem gövdeyi hem ölçümü tek istekte almanın üç kalıbı:**

```bash
# 1 - cleanest: body to a file, measurements to stdout
curl -sS --max-time 10 -o body.json \
     -w "%{http_code} %{time_total}\n" "$URL"

# 2 - single variable: measurements appended as the last line
out=$(curl -sS --max-time 10 -w "\n%{http_code} %{time_total}" "$URL")
body=$(printf '%s' "$out" | sed '$d')     # everything but the last line
stats=$(printf '%s' "$out" | tail -n 1)

# 3 - WRONG: this sends the request twice and measures a different one
curl -s -o /dev/null -w "%{time_total}\n" "$URL"
body=$(curl -s "$URL")
```

Üçüncüsü sık yapılır ve iki ayrı hatası var: iki kat istek atar (rate limit ölçümünde
sayacı bozar) ve ölçtüğün istek ile okuduğun gövde **farklı isteklerdir**.

---

## 5. Ne kaydedilir — ölçüm satırının anatomisi

Ekrana bakıp göz kararı yorum yapmak ölçüm değildir. Ölçüm **makine tarafından
özetlenebilir** olmak zorundadır.

Her istek için bir satır, CSV/TSV:

```
seq,epoch_ms,http_code,api_error,ttfb,total,bytes
1,1786600000123,200,,0.184,0.211,31876
2,1786600000398,200,,0.176,0.203,31876
```

| Kolon | Neden |
|---|---|
| `seq` | Kaçıncı istekte olay oldu |
| `epoch_ms` | **Aritmetik yapılabilir zaman.** İnsan okunur tarih özet çıkarmayı zorlaştırır |
| `http_code` | Referans için |
| `api_error` | **Gövdedeki `error` alanı.** Last.fm'de asıl sinyal burada (not 11 §7) |
| `ttfb`, `total` | Gecikme |
| `bytes` | Payload boyutu — beklenmedik biçimde küçülürse hata sayfası gelmiş olabilir |

Şema tasarımının aynı mantığı burada da geçerli: her kolonun cevapladığı bir soru var
(not 15 §1).

---

## 6. Özet istatistik — ortalama neden yalan söyler

Gecikme dağılımı **sağa çarpıktır**: çoğu istek hızlıdır, birkaçı çok yavaştır (yeniden
iletim, GC duraklaması, soğuk önbellek). Tek bir 3 saniyelik gözlem, 20 ölçümün
ortalamasını görünür biçimde yukarı çeker — ama medyanı oynatmaz.

Bu yüzden sektörde ortalama değil **yüzdelikler** kullanılır: p50 (medyan), p95, p99.
SLA'ler ve uyarı eşikleri neredeyse her zaman p95/p99 üzerine yazılır — çünkü kullanıcı
deneyimini bozan şey ortalama değil, kuyruktur.

**Dürüst uyarı — 20 örnekle p95 hesaplama.** 20 sıralı gözlemde p95, 19. elemandır: tek bir
gözlem. Gürültüdür, istatistik değildir. Anlamlı bir p95 için kabaca 100+, p99 için 1000+
örnek gerekir. 20 örnekle dürüstçe söyleyebileceklerin: **min, medyan, maks** ve "hepsi
şu değerin altındaydı".

> Az örnekle çok hassas istatistik raporlamak, ölçüm yapmamaktan daha kötüdür — çünkü
> yanlış bir güven üretir.

Shell'den özet:

```bash
# median of column 6 (total), from a CSV without header
cut -d, -f6 measurements.csv | sort -n | awk '{a[NR]=$1} END {print a[int(NR/2)+1]}'
```

Ama dürüst tavsiye: birkaç sayıdan fazlası gerekiyorsa Python'a geç. `awk` ile percentile
hesaplamak yazması eğlenceli, okuması ve doğrulaması zordur.

---

## 7. Profesyoneller bunu nasıl yapıyor

Önce yaygın araçlar ve **her birinin bu iş için neden yanlış olduğu**:

| Araç | Ne için tasarlandı | 1.8'de neden yanlış |
|---|---|---|
| `hyperfine` | CLI komut benchmark'ı; ısınma turu, outlier tespiti, istatistik | HTTP semantiği yok — gövdedeki `error: 29`'u göremez |
| `ab` (ApacheBench) | Eski HTTP yük testi | Doygunluk hedefler; API key'ini yaktırır |
| `wrk`, `hey`, `k6`, `locust` | Modern yük/performans testi | Aynı — **kırmak için** tasarlanmışlar |
| `vegeta -rate=5/s` | **Sabit hızda** yük üretimi | **İstisna** — sabit hız, limit sondajının doğru şeklidir |
| `curl` + shell döngüsü | Tek seferlik keşif | **Burada doğru** |
| Python + `httpx` | Gövde parse + karar mantığı gereken ölçüm | 1.8 için de meşru, hatta daha temsili |

**Dürüst cevap — sektörde gerçekte ne oluyor:**

1. **Kendi servisini** test ederken `k6`/`vegeta`/`locust` kullanılır. Amaç sistemi
   sınırına kadar zorlamaktır ve sistem senindir.

2. **Başkasının API'sinin** limitini keşfederken yük testi aracı kullanılmaz. Sebep basit:
   o araçlar doyurmak için yazılmış, sen doyurmamak zorundasın. Kullanılan şey küçük bir
   script'tir — tam da senin yazacağın şey.

3. Ve çoğu zaman **hiç sondaj yapılmaz**: dokümandaki limit alınır, altında kalınacak
   şekilde throttle yazılır, gerçek davranış **prod'da pasif olarak** izlenir. Yani
   profesyonel refleks "ölçmek için ekstra istek atmak" değil, **zaten atılan isteklerin
   süresini ve hata kodlarını loglamaktır.** Ölçüm ayrı bir iş değil, pipeline'ın kalıcı
   bir özelliğidir.

Üçüncü madde bu projede 3.x ve 6.x'e taşınacak: her isteğin süresi ve hata kodu
loglanırsa, rate limit davranışı bir daha hiç "ölçülmek" zorunda kalmaz — sürekli
bilinir hale gelir.

> **Akılda kalması gereken:** Tek seferlik sondaj bir başlangıç değeridir. Kalıcı cevap
> gözlemlenebilirliktir (observability).

---

## 8. Yaygın yanılgılar

| Yanılgı | Gerçek |
|---|---|
| `for i in {1..$N}` çalışır | Çalışmaz. Brace expansion değişken genişletmesinden önce olur. |
| `-s` sadece kozmetik | Hayır. Progress metresi stderr'i kirletir, ölçüm çıktısını bozar. |
| `read` yeterli, `-r` süs | Hayır. `-r`'siz `read` ters bölüyü yer, Windows yollarını bozar. |
| Ortalama gecikme yeterli | Hayır. Dağılım çarpık; medyan ve maks daha dürüst. |
| `curl` döngüsü Python istemciyi temsil eder | Hayır. Bağlantı yeniden kullanımı yok, sistematik olarak yavaş ölçer. |
| PowerShell'de `ForEach-Object` içinde `break` çalışır | Çalışmaz. Erken çıkış gerekiyorsa `foreach`. |
| HTTP 200 gördüm, istek başarılı | Kaynağa bağlı. Last.fm'de hata gövdededir (not 11 §7). |
| Döngüye üst sınır koymak gereksiz, koşul zaten var | Dış dünyaya istek atan döngüde üst sınır bir emniyet kemeridir. |

---

## 9. Kontrol listesi — bir şeyi ölçmeden önce

- [ ] Bu ölçümün **yan etkisi** var mı? Ölçtüğüm sistem bana mı ait?
- [ ] Sistem cevabı zaten söylüyor mu? (response header'ları, `/limits` endpoint'i, doküman)
- [ ] Ölçümün **üst sınırı** var mı — döngü en kötü ihtimalle kaç kez döner?
- [ ] Başarısızlık sinyalini doğru yerden mi okuyorum? (status kodu mu, gövde mi)
- [ ] Her gözlem **makine okunur** biçimde kaydediliyor mu?
- [ ] Ölçüm aracı, ölçmek istediğim gerçek istemciyi temsil ediyor mu?
- [ ] Temsil etmiyorsa, **yanlılığı ölçümün yanına yazdım mı**?
- [ ] Örnek sayım, raporlayacağım istatistiği taşıyor mu?
- [ ] `--max-time` gibi bir zaman tavanı var mı — asılı istek döngüyü kilitler mi?

---

## 10. Mülakat

**"Bir API'nin rate limit'ini nasıl bulursun?"**

> Önce bedava olan yolları tüketirim: response header'larında `X-RateLimit-*` veya
> `Retry-After` var mı, dokümanda bir rakam var mı, varsa kapsamı ne — IP başına mı, key
> başına mı. Sonra pasif ölçerim: normal ardışık kullanımda gerçekte kaç istek/sn
> yapıyorum. Çoğu zaman zaten limitin altında çıkar ve sondaj hiç gerekmez. Aktif sondaja
> ancak gerekirse geçerim, o zaman da düşükten başlayıp kademeli artırır ve ilk sinyalde
> dururum — çünkü kendime ait olmayan bir sistemde sondajın bedeli hesabın banlanmasıdır.

**"Gecikme ölçümünde ortalama mı kullanırsın?"**

> Hayır, dağılım sağa çarpık. Medyan ve p95/p99 kullanırım; SLA'ler de zaten kuyruk
> üzerine yazılır. Ama örnek sayısına dikkat ederim — 20 gözlemle p95 raporlamak tek bir
> gözlemi istatistik gibi sunmaktır.

**"`curl` ile ölçtüğün gecikme, uygulamanın göreceği gecikme midir?"**

> Hayır, ve bu fark önemli. Döngüdeki her `curl` ayrı süreç olduğu için her turda TCP ve
> TLS el sıkışmasını yeniden öder; gerçek istemci bağlantı havuzu kullanır ve bunu ikinci
> istekten sonra ödemez. `curl` ölçümü sistematik olarak kötümserdir. Bunu ya `httpx` gibi
> gerçek istemciyle ölçerek düzeltirim ya da en azından ölçümün yanına yanlılık notu
> düşerim.

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **brace expansion** | `{1..20}` gibi kalıpların listeye açılması; shell'in en erken adımlarından biri |
| **glob** | `*.json` gibi dosya adı deseni |
| **nullglob** | Eşleşme yoksa glob'un boş liste vermesini sağlayan bash seçeneği |
| **TTFB** | Time To First Byte — ilk bayt gelene kadar geçen süre; sunucunun düşünme süresi |
| **connection reuse / keep-alive** | Aynı TCP bağlantısı üzerinden birden çok istek göndermek |
| **connection pool** | İstemcinin açık bağlantıları saklayıp yeniden kullandığı havuz |
| **percentile (p50/p95/p99)** | Gözlemlerin %50/%95/%99'unun altında kaldığı değer |
| **sağa çarpık dağılım** | Çoğu değer küçük, az sayıda çok büyük değer olan dağılım |
| **saturation testing** | Sistemi sınırına kadar zorlayan yük testi |
| **observability** | Sistemin davranışını dışarıdan sürekli gözlemleyebilme özelliği |
| **throttle** | İstek hızını kasıtlı olarak sınırlamak |

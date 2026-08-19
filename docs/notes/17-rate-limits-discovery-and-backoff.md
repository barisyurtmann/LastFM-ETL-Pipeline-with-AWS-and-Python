# 17 — Rate limit: keşif, algoritmalar, backoff

> **Bu notun sorusu:** *Bir API'nin hız sınırı nasıl bulunur, nasıl saygı gösterilir,
> takılınca ne yapılır?*
>
> [Not 16](16-shell-loops-and-measurement.md) mekaniği anlatır (döngü, `curl -w`, istatistik).
> Bu not o mekaniği belirli bir probleme uygular ve üstüne algoritma + backoff ekler.
>
> Örnekler **bash**. Hepsi çalıştırılabilir, kopyala-yapıştır değil kopyala-oku-çalıştır.

> **Kısa cevap** — Bir API'nin rate limit'i nasıl bulunur ve takılınca nasıl davranılır?
>
> 1. Throttle ve retry ayrı mekanizmadır; tek başına retry sistemin normal modunu "hata al, bekle" yapar.
> 2. `Retry-After` gerçek RFC 9110 standardı, `X-RateLimit-Reset` de facto: epoch mu kalan saniye mi API'ye göre değişir.
> 3. Sabit `sleep` hedef aralığa eklenir ve gerçek hızı düşürür; doğrusu geçen süreyi düşüp kalanı uyumaktır.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

---

## 1. Rate limit bir hata değil, bir sözleşme

`429 Too Many Requests` bir bug değil. Sunucunun sana "yavaşla" demesi. Karşı taraf seni
reddetmiyor, **sıraya sokuyor**.

Junior refleksi: rate limit'i bir istisna olarak görüp `try/except` ile sarmak. Bu yarım
çözümdür, çünkü iki ayrı mekanizma gerekir:

| Mekanizma | Ne zaman devreye girer | Amacı |
|---|---|---|
| **Proaktif throttle** | Her istekte, sürekli | Sınıra **hiç** takılmamak |
| **Reaktif retry** | Sınıra takıldıktan sonra | Takıldığında kaybetmemek |

Sadece retry yazarsan, sistemin normal çalışma modu "hata al, bekle, tekrar dene" olur.
Bu çalışır ama gürültülüdür: log'lar hatayla dolar, gerçek hatalar bu gürültünün içinde
kaybolur, ve karşı taraf seni kötü davranan istemci olarak görür. Sadece throttle yazarsan
da yetmez — başkasının trafiği, ağ dalgalanması veya limitin değişmesi seni yine vurur.

> **İkisi birden yazılır.** Throttle normal hâldir, retry emniyet ağıdır.

---

## 2. Keşif protokolü — dört aşama, ucuzdan pahalıya

**Kural: riski olmayan aşamalar tüketilmeden riskli aşamaya geçilmez.**

| # | Aşama | Risk | Ne öğretir |
|---|---|---|---|
| 1 | Response header'ları | Sıfır | API limiti kendisi söylüyor olabilir |
| 2 | Doküman / ToS | Sıfır | Sayı, kapsam, ceza |
| 3 | Pasif ölçüm | Sıfır | Normal kullanımda ulaşılan gerçek hız |
| 4 | Aktif sondaj | **Var** | Sınırın gerçek yeri |

Çoğu junior doğrudan 4'e atlar. Oysa 1–3 çoğu zaman cevabı verir ve 4'ü gereksiz kılar.

### Aşama 1 — Header'lar

```bash
curl -sS -D - -o /dev/null \
  "https://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=${LASTFM_API_KEY}&format=json&limit=1" \
  | grep -i -E 'ratelimit|retry-after|x-rate' \
  || echo "no rate-limit headers present"
```

Üç ayrıntı:

- `-D -` header'ları stdout'a akıtır, `-o /dev/null` gövdeyi atar.
- `grep -i` **şart**: HTTP header adları büyük/küçük harfe duyarsızdır (RFC 9110) ve HTTP/2
  bunları zorunlu olarak küçük harfe çevirir. `grep 'X-RateLimit'` HTTP/2'de hiçbir şey bulmaz.
- `|| echo ...` **şart**: `grep` eşleşme bulamazsa exit code `1` döner. `set -e` altında
  bu script'i öldürür (not 12 §4). "Bulamamak" burada bir hata değil, geçerli bir sonuçtur.

Aranan header'lar ve **gerçek standart durumları**:

| Header | Durum | Anlamı |
|---|---|---|
| `Retry-After` | **Gerçek standart** — RFC 9110 §10.2.3 | Kaç saniye bekle (veya HTTP-date) |
| `RateLimit-Limit` / `-Remaining` / `-Reset` / `-Policy` | **IETF taslağı**, henüz RFC değil (`draft-ietf-httpapi-ratelimit-headers`) | Kota, kalan, sıfırlanma |
| `X-RateLimit-*` | **De facto**, hiçbir standart yok | Her API kendi yorumu |

Bu ayrım pratik sonuç doğurur:

> `Retry-After`'ın anlamına güvenebilirsin. `X-RateLimit-Reset`'in **epoch mı yoksa kalan
> saniye mi** olduğunu her API için ayrı okumak zorundasın.

GitHub epoch saniye verir, başka API'ler kalan saniye verir. Aynı isim, farklı anlam.
Bunu varsaymak, üretimde saatlerce yanlış beklemek demektir.

### Aşama 2 — Doküman

Aranacak altı şey. **Sayı bunlardan sadece biri:**

| # | Soru | Neden önemli |
|---|---|---|
| 1 | Sayı ne? | Bariz olan |
| 2 | **Kapsamı ne?** | IP başına mı, key başına mı, kullanıcı başına mı, endpoint başına mı |
| 3 | Pencere ne? | Saniye, dakika, gün — ve **kayan mı sabit mi** |
| 4 | Burst izni var mı? | "Ortalama" ifadesi genelde burst izni demektir |
| 5 | Aşınca ne olur? | Reddedilir mi, yavaşlatılır mı, **banlanır mı** |
| 6 | Yükseltme yolu var mı? | Yazılı izin, ücretli plan |

2. madde en sık atlanan ve en pahalıya patlayandır. "5 istek/sn" cümlesi, *neyin* 5 isteği
cevaplanmadan tasarım girdisi değildir:

| Kapsam | Mimari sonucu |
|---|---|
| IP başına | Farklı ortamlar (ev, iş, Lambda) ayrı kovalar. Ama ortak NAT arkasında başkasının trafiği seni vurur. |
| Key başına | Tüm ortamlar aynı kovayı paylaşır. IP değiştirmek **hiçbir şey kazandırmaz**. |
| Kullanıcı başına | Çok kiracılı sistemde kiracı başına throttle gerekir |
| Endpoint başına | Tek bir global throttle yetmez, endpoint bazlı kova gerekir |

**Ve dokümanın dürüst sınırı:** doküman eskir, kod eskimez. Belgelenen limit ile gerçek
limit ayrışabilir — genelde gerçek limit daha sıkıdır (kötüye kullanım sonrası sessizce
kısılmıştır). Doküman bir başlangıç değeridir, doğrulanmış gerçek değil.

### Aşama 3 — Pasif ölçüm

Amacı sınırı bulmak **değil**: normal ardışık kullanımda gerçekte kaç istek/sn yapıldığını
görmek. Çoğu zaman sonuç "zaten limitin çok altındayım" çıkar ve 4. aşama düşer.

```bash
#!/usr/bin/env bash
# Passive rate measurement: run N sequential requests at natural speed and
# record what actually happens. This does not try to exceed any limit.
set -euo pipefail

: "${LASTFM_API_KEY:?set LASTFM_API_KEY first - see note 11 section 3}"

BASE="https://ws.audioscrobbler.com/2.0/"
N=20
OUT="ratelimit-probe.csv"

echo "seq,epoch_ms,http_code,ttfb,total,bytes,api_error" > "$OUT"

start_ms=$(date +%s%3N)
count=0

for i in $(seq 1 "$N"); do
  body_file=$(mktemp)

  # Body goes to a file; -w writes the measurements to stdout.
  # --max-time is mandatory: one hung request would otherwise stall the loop.
  stats=$(curl -sS --max-time 10 \
    -o "$body_file" \
    -w '%{http_code},%{time_starttransfer},%{time_total},%{size_download}' \
    "${BASE}?method=chart.gettoptracks&api_key=${LASTFM_API_KEY}&format=json&limit=20&page=${i}")

  # Last.fm answers HTTP 200 even on failure and puts the real result in the
  # body, so the status code alone cannot distinguish success from throttling.
  api_error=$(grep -o '"error"[[:space:]]*:[[:space:]]*[0-9]\+' "$body_file" \
              | grep -o '[0-9]\+$' || true)

  printf '%d,%s,%s,%s\n' "$i" "$(date +%s%3N)" "$stats" "${api_error:-}" >> "$OUT"
  rm -f "$body_file"
  count=$((count + 1))

  if [ "${api_error:-}" = "29" ]; then
    echo "throttled at request $i - stopping" >&2
    break
  fi
done

end_ms=$(date +%s%3N)

awk -v s="$start_ms" -v e="$end_ms" -v n="$count" 'BEGIN {
  d = (e - s) / 1000
  printf "requests=%d  elapsed=%.1fs  achieved=%.2f req/s\n", n, d, n / d
}'

# Latency summary. With ~20 samples only min / median / max are honest;
# a p95 computed from 20 points is a single observation, not a statistic.
tail -n +2 "$OUT" | cut -d, -f5 | sort -n | awk '{v[NR]=$1} END {
  printf "total time: min=%.3fs  median=%.3fs  max=%.3fs\n", v[1], v[int((NR+1)/2)], v[NR]
}'
```

Dikkat edilecek yerler:

| Satır | Neden böyle |
|---|---|
| `: "${VAR:?mesaj}"` | Değişken tanımsızsa script **başlamadan** anlaşılır hatayla durur |
| `set -euo pipefail` | Hata varsa dur, tanımsız değişkende dur, pipe'ın ortasındaki hata yutulmasın |
| `--max-time 10` | Asılı tek bir istek tüm döngüyü kilitler |
| `|| true` | `grep` eşleşme bulamazsa `1` döner; burada bu hata değil |
| `date +%s%3N` | Milisaniye epoch. GNU `date` özelliğidir — Git Bash'te var, macOS'un BSD `date`'inde yok |
| `sort -n` sonra `awk` | `gawk`'ın `asort`'u her yerde yok; sıralamayı `sort`'a yaptırmak taşınabilir |

### Aşama 4 — Aktif sondaj

**Önce emniyet kuralları. Bunlar öneri değil.**

1. Belgelenen limitin **altında** kal. Sondaj limiti aşmak için değil, davranışı görmek için.
2. **Alttan yaklaş.** Düşük hızdan başla, kademeli artır. Yukarıdan aşağı binary search yapma.
3. **İlk sinyalde dur.** Bir kere doğrulamak yeter; "acaba tesadüf müydü" diye tekrarlama.
4. **Sert üst sınır koy.** Toplam istek sayısı ve maksimum hız, kodun içinde sabit olsun.
5. Ölçtüğün sistem sana ait değilse, bunu **bir kere** yap ve sonucu yaz.

Last.fm'de aşma cezası soyut değil: hata kodu **26 — "Your API key has been banned"**.

```bash
#!/usr/bin/env bash
# Active probe. Ramps request rate from 1/s upward and stops at the first
# throttle signal. Hard caps below are deliberate and must not be raised
# casually: this runs against a system we do not own.
set -euo pipefail

: "${LASTFM_API_KEY:?set LASTFM_API_KEY first}"

BASE="https://ws.audioscrobbler.com/2.0/"
MAX_RATE=4          # stay below the documented 5 req/s
BURST=10            # requests sent at each rate step
MAX_TOTAL=60        # absolute ceiling across the whole run
URL="${BASE}?method=chart.gettoptracks&api_key=${LASTFM_API_KEY}&format=json&limit=1"

sent=0

for rate in $(seq 1 "$MAX_RATE"); do
  interval=$(awk -v r="$rate" 'BEGIN{printf "%.4f", 1 / r}')
  echo "--- probing at ${rate} req/s (interval ${interval}s)"

  for _ in $(seq 1 "$BURST"); do
    if [ "$sent" -ge "$MAX_TOTAL" ]; then
      echo "hit MAX_TOTAL - stopping"; exit 0
    fi

    t0=$(date +%s%3N)
    payload=$(curl -sS --max-time 10 "$URL")
    sent=$((sent + 1))

    api_error=$(printf '%s' "$payload" \
                | grep -o '"error"[[:space:]]*:[[:space:]]*[0-9]\+' \
                | grep -o '[0-9]\+$' || true)

    if [ -n "${api_error:-}" ]; then
      echo "signal at rate=${rate} after ${sent} requests: error ${api_error}"
      exit 0                      # rule 3: stop at the first signal
    fi

    # Sleep only the remainder of the interval, not a flat amount.
    t1=$(date +%s%3N)
    remain=$(awk -v a="$t0" -v b="$t1" -v i="$interval" \
             'BEGIN{ r = i - (b - a) / 1000; print (r > 0) ? r : 0 }')
    sleep "$remain"
  done
done

echo "no throttle signal up to ${MAX_RATE} req/s across ${sent} requests"
```

---

## 3. "Kalan süre kadar uyu" — sık yapılan hız hatası

Yukarıdaki iki script'te geçen kalıp önemli ve genelde yanlış yazılır.

```bash
# WRONG: the sleep is added to the latency, so the real rate is much lower.
curl ... ; sleep 0.25          # 0.25s + 0.30s latency = 1.8 req/s, not 4

# RIGHT: sleep only what is left of the target interval.
t0=$(date +%s%3N)
curl ...
t1=$(date +%s%3N)
remain=$(awk -v a="$t0" -v b="$t1" -v i=0.25 'BEGIN{r=i-(b-a)/1000; print (r>0)?r:0}')
sleep "$remain"
```

Sabit `sleep`, hedef aralığa **eklenir**; kalan-süre uykusu hedef aralığı **doldurur**.
Fark, gecikme büyüdükçe büyür — ve gecikme tam da kontrol edemediğin şeydir.

`sleep 0.25` ondalık kabul eder çünkü GNU coreutils uzantısıdır (Git Bash'te var). POSIX
`sleep` yalnızca tam sayı alır; taşınabilirlik gerekiyorsa Python'a geçmek daha temizdir.

---

## 4. Rate limit algoritmaları ve nasıl ayırt edilir

Sunucunun hangi algoritmayı kullandığını bilmek, doğru backoff'u seçmeni sağlar.

| Algoritma | Nasıl çalışır | Dışarıdan belirtisi |
|---|---|---|
| **Fixed window** | Duvar saatinin sınırında sıfırlanır (her dakikanın başı) | Sınırda **çift burst**: pencerenin sonunda N + başında N, kısa sürede 2N geçebilir |
| **Sliding window log** | Her isteğin zamanı tutulur, tam olarak N/pencere | Kesin ama sunucuya pahalı; nadir |
| **Sliding window counter** | İki komşu pencerenin ağırlıklı ortalaması | Fixed'in çift-burst açığı yok, yaklaşık sonuç |
| **Token bucket** | Kova sabit hızda dolar, her istek 1 token harcar; kova kapasitesi = **burst izni** | Bir süre serbest burst, sonra sabit hıza oturma |
| **Leaky bucket** | Çıkış sabit hızda akar, fazlası kuyrukta bekler veya düşer | İstekler **reddedilmez, gecikir** |

**Nasıl ayırt edilir:** sınıra takıldıktan sonra **ne zaman açıldığını** ölç.

| Gözlem | Muhtemel algoritma |
|---|---|
| Duvar saatinin tam sınırında açıldı (`:00`, `:15`) | Fixed window |
| Takıldıktan tam N saniye sonra açıldı | Sliding window |
| Kademeli açıldı — önce tek istek geçti, sonra daha çok | **Token bucket** |
| Hiç reddedilmedi ama gecikmeler büyüdü | Leaky bucket / kuyruk |

```bash
# After being throttled: poll once per second until the first success,
# and record how long recovery took. One request per second is polite.
t0=$(date +%s)
while true; do
  payload=$(curl -sS --max-time 10 "$URL")
  if ! printf '%s' "$payload" | grep -q '"error"'; then
    echo "recovered after $(( $(date +%s) - t0 ))s"
    break
  fi
  sleep 1
done
```

**Last.fm için tahmin — ve tahmin olduğunu belirtiyorum:** "saniyede 5, 5 dakikalık ortalama
üzerinden" ifadesi **token bucket**'a benziyor (ortalama = dolum hızı, ortalamanın üstünde
kısa süreli tolerans = kova kapasitesi). Ama bu ölçülmedi, sadece ifadenin şeklinden çıkan
bir okuma. Doğrulanmadan tasarım dayanağı yapılmaz.

---

## 5. Takılınca: backoff

### Sabit bekleme neden kötü

```bash
sleep 5    # every client that got throttled wakes up at the same moment
```

N istemci aynı anda takılır, hepsi aynı süre bekler, hepsi aynı anda tekrar vurur. Sunucu
tam toparlanırken ikinci dalga gelir. Buna **thundering herd** denir ve rate limit'i
çözmez, ritmini sabitler.

### Üstel backoff + jitter

```
delay = base * 2^attempt      ... ve üstüne rastgelelik
```

Yaygın olarak atıfta bulunulan sınıflandırma (AWS Architecture Blog'un "Exponential Backoff
and Jitter" yazısından yayılmıştır — **bir RFC değil**, ama fiilen referans kabul edilir):

| Strateji | Formül | Yorum |
|---|---|---|
| Jitter yok | `min(cap, base * 2^n)` | Sürü hâlâ senkron |
| **Full jitter** | `random(0, min(cap, base * 2^n))` | Genelde en iyi sonuç veren |
| Equal jitter | `h + random(0, h)`, `h = min(cap, base*2^n)/2` | Daha öngörülebilir |
| Decorrelated | `min(cap, random(base, prev * 3))` | Uzun kuyruklarda iyi |

```bash
# Full jitter: sleep a random amount in [0, min(cap, base * 2^attempt)].
delay=$(awk -v b=1 -v c=60 -v n="$attempt" -v r="$RANDOM" 'BEGIN{
  x = b * (2 ^ n); if (x > c) x = c
  printf "%.2f", (r / 32767) * x
}')
sleep "$delay"
```

`$RANDOM` bash'e özgüdür, `0..32767` aralığında değer verir.

### `Retry-After` her zaman kazanır

Sunucu kaç saniye beklemen gerektiğini **söylüyorsa**, kendi hesabını ona tercih etme.

```bash
retry_after=$(curl -sS -D - -o /dev/null "$URL" \
              | grep -i '^retry-after:' \
              | tr -d '\r' \
              | awk '{print $2}')
```

`tr -d '\r'` **atlanamaz**: HTTP header satırları CRLF ile biter, `\r` değerin sonuna
yapışır ve `sleep 30<CR>` hata verir. Bu, not 03'teki satır sonu konusunun beklenmedik bir
yerde karşına çıkmasıdır.

`Retry-After` iki biçimde gelebilir (RFC 9110): saniye sayısı **veya** HTTP-date. İkisini
de karşılamayan kod, ikinci biçimi gördüğü gün patlar.

### İki üst sınır, biri yetmez

| Sınır | Neden gerekli |
|---|---|
| `max_attempts` | Sonsuz döngüyü engeller |
| `max_elapsed_time` | Üstel büyümede 10 deneme saatlere ulaşabilir; toplam süre de sınırlanmalı |

### Hangi hata retry edilir

| Durum | Retry? | Gerekçe |
|---|---|---|
| `429` | Evet, backoff ile | Geçici |
| `500` `502` `503` `504` | Evet | Sunucu tarafı geçici |
| `408` | Evet | İstek zaman aşımı |
| Ağ timeout / connection reset | Evet | Taşıma katmanı |
| `400` `401` `403` `404` `422` | **Hayır** | Aynı istek asla başarılı olmayacak |
| Last.fm `8` (generic), `11` (offline), `16` (temporary) | Evet | Geçici/backend |
| Last.fm `29` (rate limit) | Evet, backoff ile | Geçici |
| Last.fm `6` (param), `10` (bad key), `26` (banned) | **Hayır** | Girdi/kimlik hatası; tekrar denemek zarar verir |

> **Retry edilmeyecek bir hatayı retry etmek, hatayı düzeltmez — sadece geciktirir ve
> log'u kirletir.** 401'i beş kere denemek, beşinci seferde şifreyi öğrenmez.

### Idempotency uyarısı

Retry yalnızca istek **idempotent** ise güvenlidir. `GET` doğası gereği güvenlidir. `POST`
değildir: timeout aldığın istek sunucuda başarılı olmuş olabilir, retry ikinci bir kayıt
yaratır. Ödeme, sipariş, mesaj gönderme gibi işlemlerde retry ancak **idempotency key** ile
yapılır.

Bu projede tüm istekler `GET` olduğu için sorun yok — ama bu bir şans, bir tasarım değil.

---

## 6. Proaktif throttle — asıl çözüm

Retry, hata **aldıktan sonra** devreye girer. Throttle hiç almaman içindir.

En basit doğru hâli, §3'teki "kalan süre kadar uyu" kalıbıdır. Üretim kodunda genelde bir
**token bucket** istemci tarafında da uygulanır: kova sunucununkinden biraz daha yavaş
dolar, böylece sunucunun sınırına hiç dokunmazsın.

Hedef hız seçimi:

> Belgelenen limit bir **tavandır, hedef değildir.** Tavanın %50–70'i tipik bir hedeftir.

Sebebi: senin ölçtüğün an ile üretimin çalıştığı an aynı değil. Ağ yavaşlar, sunucu
limiti sıkar, aynı IP'den başka bir şey istek atar. Tavanda çalışan sistem, ilk
dalgalanmada limitin üstüne çıkar.

---

## 7. Yaygın yanılgılar

| Yanılgı | Gerçek |
|---|---|
| Rate limit'e takılmak bir bug'dır | Hayır, sunucunun normal bir cevabıdır. Bug, ona doğru tepki vermemektir. |
| Retry yazdım, iş bitti | Hayır. Throttle olmadan retry, sistemin normal modunu "hata al ve bekle" yapar. |
| Sabit bekleme yeterli | Hayır. Thundering herd'ü sabitler. Jitter şart. |
| Tüm hatalar retry edilir | Hayır. `401`/`403`/`404` asla düzelmez. |
| `X-RateLimit-Reset` her API'de aynı anlama gelir | Hayır. Epoch mı kalan saniye mi — API'ye göre değişir. |
| `grep 'X-RateLimit'` header'ı bulur | HTTP/2'de bulmaz, header adları küçük harftir. `grep -i` şart. |
| `Retry-After` sadece saniyedir | HTTP-date de olabilir (RFC 9110). |
| Doküman ne diyorsa gerçek odur | Doküman eskir; gerçek limit genelde daha sıkıdır. |
| HTTP 200 aldım, kısıtlanmadım | Kaynağa bağlı — Last.fm hatayı gövdede taşır (not 11 §7). |
| Sondaj yapmadan limit bilinmez | Çoğu zaman header veya doküman yeter; sondaj son çaredir. |

---

## 8. Kontrol listesi — yeni bir API'ye bağlanırken

- [ ] Response header'larında `retry-after` / `ratelimit-*` / `x-ratelimit-*` var mı (`grep -i`)
- [ ] Dokümanda: sayı, **kapsam**, pencere, burst, ceza, yükseltme yolu
- [ ] Kapsam IP mi key mi — bu, dağıtık çalıştırma tasarımını belirler
- [ ] Pasif ölçüm: normal ardışık kullanımda ulaşılan gerçek hız ne
- [ ] Hedef hız, belgelenen tavanın %50–70'i olarak seçildi mi
- [ ] Throttle **ve** retry ayrı ayrı yazıldı mı
- [ ] Backoff üstel ve **jitter'lı** mı
- [ ] `Retry-After` varsa kendi hesabımı eziyor mu
- [ ] `max_attempts` **ve** `max_elapsed_time` ikisi de var mı
- [ ] Retry edilmeyecek hatalar listesi açıkça yazıldı mı
- [ ] İstekler idempotent mi — değilse retry güvenli mi
- [ ] Kısıtlanma olayları **loglanıyor** mu (sessiz retry, sorunu görünmez yapar)

---

## 9. Mülakat

**"Bir API'nin rate limit'ini nasıl bulursun?"**

> Önce bedava olanları tüketirim: response header'larında `Retry-After` veya `RateLimit-*`
> var mı, dokümanda sayı ve **kapsam** ne. Kapsamı özellikle sorarım — IP başına mı key
> başına mı, çünkü bu dağıtık çalıştırma tasarımını değiştirir. Sonra pasif ölçerim: normal
> ardışık kullanımda kaç istek/sn yapıyorum. Çoğu zaman zaten limitin altında çıkar ve
> sondaja hiç gerek kalmaz. Aktif sondaja ancak gerekirse geçerim; o zaman da alttan
> yaklaşır, sert üst sınır koyar ve ilk sinyalde dururum — çünkü bana ait olmayan bir
> sistemde sondajın bedeli hesabın banlanmasıdır.

**"Rate limit'e takılan bir istemci nasıl davranmalı?"**

> İki ayrı mekanizma olmalı. Proaktif throttle sınıra hiç dokunmamak için, reaktif retry
> yine de takılırsa diye. Retry üstel ve jitter'lı olmalı, yoksa tüm istemciler senkron
> uyanıp ikinci bir dalga yaratır. Sunucu `Retry-After` gönderiyorsa o her zaman kendi
> hesabımı ezer. Ve retry edilecek hatalarla edilmeyecekler ayrılmalı — `401`'i beş kere
> denemek hiçbir şey kazandırmaz, sadece log'u kirletir.

**"Backoff'ta jitter neden gerekli?"**

> Jitter olmadan aynı anda takılan bütün istemciler aynı anda uyanır ve sunucu tam
> toparlanırken ikinci dalga gelir — thundering herd. Rastgelelik bu senkronizasyonu kırar.
> Pratikte full jitter, yani `random(0, min(cap, base * 2^n))`, çoğu senaryoda en iyi
> sonucu verir.

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **throttle** | İstek hızını istemci tarafında kasıtlı sınırlamak |
| **backoff** | Başarısızlıktan sonra beklemek; genelde her denemede artan süre |
| **jitter** | Bekleme süresine eklenen rastgelelik |
| **thundering herd** | Aynı anda uyanan çok sayıda istemcinin sunucuyu yeniden vurması |
| **token bucket** | Sabit hızda dolan, her istekte bir token harcanan kova; kapasitesi burst iznidir |
| **leaky bucket** | Çıkışı sabit hızda akan kuyruk; fazlası bekler veya düşer |
| **fixed / sliding window** | Sayacın duvar saatiyle mi kayan pencereyle mi sıfırlandığı |
| **burst** | Kısa sürede ortalamanın üstünde istek gönderebilme izni |
| **idempotent** | Aynı isteği iki kez göndermenin bir kez göndermekle aynı sonucu vermesi |
| **idempotency key** | İsteği tekilleştirmek için istemcinin ürettiği kimlik |
| **429** | `Too Many Requests` — sunucunun "yavaşla" cevabı |

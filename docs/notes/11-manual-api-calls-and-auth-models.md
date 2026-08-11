# 11 — API'yi elle çağırmak ve auth modelleri

> Adım 1.2 · 2026-08-11

Kod yazmadan önce API'yi elle çağırmak, her ciddi entegrasyonun ilk adımıdır. Bu not
üç şeyi toplar: **neden** elle çağrılır, sırrı **komut satırına sokmadan** nasıl çağrılır,
ve karşına çıkacak **auth modellerinin her birinde** bunun nasıl yapıldığı.

---

## 1. Neden elle çağırmalı

`requests` ile yazarsan aynı anda iki şeyi test etmiş olursun: API'nin davranışını ve
kendi kodunu. Bir şey patladığında hangisi olduğunu bilemezsin.

`curl` senin kodunu denklemden çıkarır. Geriye sadece API'nin gerçeği kalır.

Sektörde bu adıma **API exploration** ya da **spike** denir. Amacı kalıcı kod üretmek
değil, bilgi üretmek: gerçek payload nasıl görünüyor, hata nasıl geliyor, hangi alanlar
gerçekten dolu.

**Junior tuzağı:** dokümantasyonu okuyup doğrudan kod yazmak. Dokümantasyon API'nin
**iddiasıdır**, payload **gerçeğidir**. İkisi sistematik olarak farklıdır — dokümanda
"integer" yazan alan string gelir, "her zaman döner" denen alan bazen `null` gelir.

**Prod'da ne kırılır:** dokümana göre yazılan şema, gerçek payload'ın kenar durumlarını
karşılamaz. Pipeline üç hafta çalışır, sonra o alanın boş geldiği ilk kayıtta patlar —
ya da daha kötüsü, patlamaz ve veriyi sessizce bozar.

---

## 2. Sır komut satırına yazılmaz

En doğal refleks şudur:

```powershell
curl.exe "http://ws.audioscrobbler.com/2.0/?method=chart.getTopArtists&api_key=abc123def"
```

Bu komut çalışır ve **API key'i diske düz metin olarak yazar.**

| Shell | Geçmiş dosyası | Davranış |
|---|---|---|
| PowerShell (PSReadLine) | `%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` | Otomatik, kalıcı, düz metin |
| bash | `~/.bash_history` | Oturum kapanınca yazılır |
| zsh | `~/.zsh_history` | Aynı |

Bu dosyalar `.gitignore`'un koruyamadığı yerdir — repo dışındadırlar ama makinede
kalıcıdırlar. Yedekleme yazılımı, senkronizasyon aracı ya da başka bir kullanıcı hesabı
onlara ulaşabilir.

### Doğru yaklaşım: sır bir değişkende yaşar

```powershell
curl.exe "http://ws.audioscrobbler.com/2.0/?method=chart.getTopArtists&api_key=$env:LASTFM_API_KEY&format=json"
```

Geçmişe giren metin `$env:LASTFM_API_KEY` — key'in kendisi değil, **adı**.

### Dürüst uyarı: bu tam çözüm değil

Değişken, komut çalışırken genişletilir. Yani gerçek key **process argümanı** olarak
sisteme gider. Linux'ta `ps aux`, Windows'ta Process Explorer o argümanı gösterebilir.

| Katman | Env var yaklaşımı korur mu |
|---|---|
| Shell geçmişi (kalıcı, diskte) | Evet |
| Process argüman listesi (anlık) | Hayır |

Tam çözüm gerektiğinde: `curl --config dosya` (URL'yi dosyadan okur), `.netrc`, ya da
sırrı header olarak stdin'den vermek. Local geliştirmede env var yeterlidir; paylaşılan
bir sunucuda değildir.

---

## 3. `.env`'i shell oturumuna yüklemek

`.env` dosyası **kendiliğinden** hiçbir yere yüklenmez. O sadece bir metin dosyasıdır;
onu okuyup ortam değişkenine çeviren bir şey olmak zorundadır. Python tarafında bunu
`pydantic-settings` yapacak (Adım 2), ama `curl` için elle yapman gerekir.

### PowerShell

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
  }
}
```

| Parça | Ne yapıyor |
|---|---|
| `Get-Content .env` | Dosyayı **satır satır** akıtır (dizi döner) |
| `ForEach-Object { }` | Her satır için blok çalışır |
| `$_` | İçinde bulunulan satır — pipeline'ın "şu anki öğe" değişkeni |
| `-match` | Regex eşleştirir; `$true`/`$false` döner **ve** `$matches`'ı doldurur |
| `$matches[1]` | Regex'teki 1. yakalama grubu (key) |
| `$matches[2]` | 2. yakalama grubu (value) |
| `.Trim()` | Baş/son boşlukları kırpar |
| `SetEnvironmentVariable` | Değişkeni oturuma yazar |

**`$_` neden var:** PowerShell'de pipeline'dan gelen her öğe `$_` (ya da uzun hâli
`$PSItem`) olarak blok içinde erişilebilir. bash'teki `while read line` döngüsünün
karşılığı.

**`$matches` neden var:** `-match` operatörü bir yan etki üretir — eşleşme başarılıysa
`$matches` adlı **otomatik değişkeni** doldurur. `$matches[0]` tüm eşleşme, `[1]`'den
itibaren yakalama grupları. Bu bir fonksiyon dönüşü değil, bilinçli bir global yan etki;
PowerShell'e özgüdür.

**`SetEnvironmentVariable` neden, `$env:X = ...` neden değil:** değişkenin **adı dinamik**.
`$env:$name` diye bir sözdizimi yok — `$env:` sabit bir isim bekler. Metot çağrısı adı
parametre olarak alabildiği için tek yol budur.

> **Kritik:** iki argümanlı çağrı değişkeni **Process** kapsamına yazar — sadece o
> terminal oturumu için geçerlidir, oturum kapanınca gider. Üçüncü argüman olarak
> `[EnvironmentVariableTarget]::User` verirsen değişken **Windows Registry'ye kalıcı
> olarak** yazılır. Sırlar için bunu asla yapma: sır o andan itibaren makinede,
> `.env` dosyasından bağımsız olarak yaşamaya başlar.

### bash / Git Bash / macOS / Linux

```bash
set -a
source .env
set +a
```

`set -a` (allexport) açıkken tanımlanan her değişken otomatik olarak **export** edilir —
yani alt süreçlere (curl'e) geçer. `set +a` bunu geri kapatır. `source` olmadan `.env`'i
çalıştırmak alt kabukta değişken tanımlar ve o kabuk kapanınca kaybolur.

---

## 4. Regex'i satır satır okumak: `^\s*([^#=]+)=(.*)$`

| Parça | Anlamı | Neden orada |
|---|---|---|
| `^` | Satır başı çapası | Eşleşme satırın ortasından başlayamasın |
| `\s*` | Sıfır veya daha fazla boşluk karakteri (space, tab) | `.env`'de girintili satır olabilir |
| `(` … `)` | Yakalama grubu (capture group) | Sonradan `$matches[n]` ile geri alınacak |
| `[^#=]+` | `#` ve `=` **dışında** bir veya daha fazla karakter | Bkz. aşağıdaki iki gerekçe |
| `=` | Düz `=` karakteri (literal) | Ayırıcı |
| `(.*)` | Herhangi bir karakter, sıfır veya daha fazla | Değerin tamamı |
| `$` | Satır sonu çapası | Satırın kalanı sarkmasın |

### `[^...]` ne demek

Köşeli parantez bir **karakter sınıfıdır**: içindekilerden herhangi biri. Baştaki `^`
işareti (yalnızca köşeli parantez içindeyken) anlamı **tersine çevirir**: "bunlar hariç".

Yani `[^#=]` = "`#` de `=` de olmayan herhangi bir karakter". Aynı `^` sembolünün
parantez dışında "satır başı", parantez içinde "değil" anlamına gelmesi regex'in klasik
kafa karıştırıcı noktalarından biridir.

### `#` neden dışlandı

Yorum satırlarını elemek için.

```
# LASTFM_API_KEY=eski_key
```

`\s*` boşlukları yer, sonra `[^#=]+` en az bir karakter ister ama karşısında `#` görür —
eşleşemez, satır sessizce atlanır. Ayrı bir "yorum mu?" kontrolü yazmaya gerek kalmaz.

### `=` neden dışlandı — asıl incelik

Değer içinde `=` geçebilir. Base64 ile biten sırlar buna klasik örnektir:

```
LASTFM_API_KEY=abc123==
```

| Regex | Key | Value | Doğru mu |
|---|---|---|---|
| `^\s*([^#=]+)=(.*)$` | `LASTFM_API_KEY` | `abc123==` | Evet |
| `^\s*(.+)=(.*)$` | `LASTFM_API_KEY=abc123` | `` | Hayır |

Sebep: `.+` **açgözlüdür** (greedy) — mümkün olduğunca çok karakter yutar, sonra
geri adım atarak `=`'i **en sondan** bulur. `[^#=]+` ise `=` görünce zorunlu olarak durur,
yani **ilk** `=` ayırıcı olur. `.env` sözleşmesi tam olarak budur: ilk `=` ayırır,
gerisi değerdir.

Alternatif yazım: `^\s*(.+?)=(.*)$` — `?` niceleyiciyi **tembelleştirir** (lazy), aynı
sonucu verir. Ama `[^#=]` niyeti daha açık ifade eder ve yorum satırını da bedavaya eler.

### Bu regex'in bilinçli sınırları

| Satır | Sonuç | Not |
|---|---|---|
| `KEY=value` | `KEY` / `value` | Beklenen |
| `# KEY=value` | Eşleşmez | İstenen davranış |
| `KEY="value"` | `KEY` / `"value"` | **Tırnaklar değere dahil** — soyulmaz |
| `export KEY=value` | `export KEY` / `value` | `export` öneki key'in parçası olur |
| `KEY=value # comment` | `KEY` / `value # comment` | Satır sonu yorumu **desteklenmez** |

Son satır tanıdık gelmeli: `.gitignore` de satır sonu yorumu desteklemiyordu ve
bu proje o yüzden bir gün kaybetti (bkz. not 01). **Bu bir tesadüf değil, bir kural:**
satır tabanlı basit config formatlarında yorum genelde yalnızca **satır başında**
geçerlidir. Aksini varsayma, dokümanına bak.

Bu sınırlar kabul edilebilir çünkü bu kod **geçici bir keşif aracı**. Kalıcı çözüm
`pydantic-settings` (Adım 2.2) — o, tırnak soymayı ve tip dönüşümünü zaten doğru yapar.
Burada asıl amaç `.env`'in sihirli bir dosya olmadığını görmek: birileri onu satır satır
okur, ayrıştırır, ortam değişkenine yazar. Hepsi bu.

---

## 5. `curl` bayrakları — pratikte kullanılanlar

| Bayrak | Ne yapar | Ne zaman |
|---|---|---|
| `-i` | Response header'larını gövdeyle birlikte yazdırır | Format/Content-Type teşhisi |
| `-I` | **Sadece** header (HEAD isteği gönderir) | Gövde gereksizken |
| `-s` | Progress çubuğunu susturur | Çıktıyı dosyaya/pipe'a yazarken |
| `-S` | `-s` ile birlikte: hataları yine de göster | `-sS` ikilisi standarttır |
| `-o dosya` | Gövdeyi dosyaya yazar | Payload kaydetme (1.4) |
| `-D -` | Header'ları ayrı akıtır (`-` = stdout) | Gövdeyi dosyaya, header'ı ekrana |
| `-H "K: V"` | İstek header'ı ekler | Bearer token, `Accept` |
| `-u user:pass` | Basic Auth | Legacy API'ler |
| `-X POST` | HTTP metodunu değiştirir | Token endpoint'leri |
| `-d "a=b"` | Gövde gönderir (otomatik POST + form content-type) | OAuth token isteği |
| `-L` | Redirect'leri takip eder | 301/302 dönen endpoint |
| `-v` | Tüm el sıkışmayı gösterir (TLS dahil) | Ağır teşhis |
| `--max-time 10` | Toplam süre limiti | Asılı kalan istek |

`-i` bu adımda kritik bir rol oynadı: aradığımız kanıt gövdede değil, **header'daydı**.

---

## 6. Windows'a özgü iki tuzak

### `curl` gerçek curl değil

Windows PowerShell 5.1'de `curl`, `Invoke-WebRequest` cmdlet'inin **takma adıdır** (alias).
Bayrakları farklıdır, çıktısı bir nesnedir, `-i` gibi bayrakları anlamaz.

Windows 10 1803'ten beri sistemde gerçek curl da vardır: `C:\Windows\System32\curl.exe`.

> **Kural: PowerShell'de daima `curl.exe` yaz.** Uzantı, alias'ı atlar.

Teşhis: `Get-Command curl` neye çözüldüğünü söyler.

### `&` karakteri URL'yi böler

Hem `cmd` hem PowerShell'de `&` özel anlam taşır (komut ayırıcı / çağırma operatörü).
Tırnaksız bir URL yazarsan shell onu birden fazla komut sanar:

```powershell
curl.exe http://host/?a=1&b=2      # BOZUK
curl.exe "http://host/?a=1&b=2"    # DOGRU
```

Bu hata sinsi çünkü **kısmi çalışır**: curl ilk parçayı alır, istek gider, cevap gelir —
ama parametrelerin bir kısmı yoktur. `format=json` böyle kaybolursa XML dönen bir cevabı
"API bozuk" diye teşhis edersin.

---

## 7. HTTP status kodu neyi söyler, neyi söylemez

Bu adımın en önemli çıkarımı:

> **HTTP status kodu "sunucu isteğimi işledi mi" sorusunu cevaplar.
> "İstediğim veriyi aldım mı" sorusunu cevaplamaz.**

Deneyle kanıtlandı: aynı endpoint'e `format=json` ile ve olmadan gidildi.

| | `format` yok | `format=json` |
|---|---|---|
| Status | `200` | `200` |
| `Content-Type` | `text/xml` | `application/json` |
| Gövde ilk karakteri | `<` | `{` |

Status kodları **aynı**. Kodun ikisini status'a bakarak ayırt etmesi imkânsızdır.
`raise_for_status()` burada sessiz kalır — çünkü sunucu açısından hata yok, sen sadece
format belirtmedin, o da varsayılanı verdi.

Sonra `response.json()` çağrılır ve şu gelir:

```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Bu mesaj problemi anlatmıyor.** Aynı mesajı boş gövdede de, HTML hata sayfasında da,
proxy blok sayfasında da alırsın. "char 0'da değer bekleniyordu" cümlesi kimseyi
`format` parametresine götürmez.

**Doğru teşhis refleksi** — hata mesajına değil gövdeye bak:

```python
print(response.status_code, response.headers.get("Content-Type"))
print(response.text[:200])
```

**Junior tuzağı:** exception mesajını teşhis sanmak. Exception, hatanın **nerede
fark edildiğini** söyler — **nerede oluştuğunu** değil. `.json()` parse ederken fark eder,
hata ise çok önce, isteği kurarken yapılmıştır.

---

## 8. Auth modelleri kataloğu

"Elle çağır" adımı evrenseldir; değişen tek şey auth modelidir. Aşağıdaki liste
karşılaşma sıklığına göre sıralı.

### Özet

| # | Model | Nerede taşınır | Örnek | Elle zorluk |
|---|---|---|---|---|
| 1 | Auth yok | — | Açık veri API'leri | Yok |
| 2 | API key — query param | URL | **Last.fm**, OpenWeather | Çok kolay |
| 3 | API key — header | Header | Çoğu SaaS (`X-API-Key`) | Çok kolay |
| 4 | Basic Auth | `Authorization: Basic` | Legacy, iç servisler | Kolay |
| 5 | Bearer token / PAT | `Authorization: Bearer` | GitHub, Slack, Notion | Kolay |
| 6 | OAuth2 client credentials | Bearer (token alındıktan sonra) | **Spotify**, Reddit | Orta — iki adım |
| 7 | OAuth2 authorization code | Bearer (kullanıcı onayından sonra) | Google, Twitter | Zor — tarayıcı şart |
| 8 | OAuth2 device code | Bearer | CLI araçları, TV uygulamaları | Orta |
| 9 | JWT / service account | Bearer (JWT takas edilerek) | Google Cloud, Firebase | Zor — imzalama |
| 10 | HMAC imza | Özel header ya da param | **AWS SigV4**, Last.fm `api_sig` | Çok zor — SDK şart |
| 11 | mTLS | TLS katmanı (sertifika) | Bankacılık, Open Banking | Orta — sertifika lazım |
| 12 | Session cookie | `Cookie` header | Eski web uygulamaları | Orta |

### 1 — Auth yok

```bash
curl -s "https://api.example.com/v1/items"
```

Genelde sıkı rate limit vardır (IP başına). Prod'da IP tabanlı kısıtlama, NAT arkasındaki
tüm ofisi aynı kovaya koyar — sessiz 429'ların klasik sebebi.

### 2 — API key, query parametresinde

```bash
curl -s "https://ws.audioscrobbler.com/2.0/?method=chart.getTopArtists&api_key=$LASTFM_API_KEY&format=json"
```

**Bu projenin modeli.** En kolay ama **güvenlik açısından en zayıf** taşıma biçimi:
URL; access log'lara, tarayıcı geçmişine, `Referer` header'ına ve proxy kayıtlarına
düşer. TLS gövdeyi ve yolu şifreler ama sunucu kendi log'una yazdığında iş işten geçmiştir.

**Pratik sonuç:** loglama yazarken URL'yi asla ham basma. Bu, Adım 3.7'nin (secret
maskeleme) doğrudan gerekçesi.

### 3 — API key, header'da

```bash
curl -s -H "X-API-Key: $API_KEY" "https://api.example.com/v1/items"
```

Aynı sırrı taşır ama URL'ye bulaşmaz. Header adı standart değildir —
`X-API-Key`, `X-Auth-Token`, `api-key`, `apikey` hepsi karşına çıkar. Dokümana bak.

### 4 — Basic Auth

```bash
curl -s -u "kullanici:parola" "https://api.example.com/v1/items"
```

curl bunu `Authorization: Basic <base64(kullanici:parola)>` header'ına çevirir.

> **Base64 şifreleme değil, kodlamadır.** Geri çevirmesi tek komuttur. Basic Auth'un
> tüm güvenliği HTTPS'e bağlıdır; HTTP üzerinde kullanmak parolayı düz metin göndermekle
> aynı şeydir.

### 5 — Bearer token (PAT)

```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "https://api.github.com/user"
```

Bugün en yaygın model. **PAT** (Personal Access Token) kullanıcı tarafından panelden
üretilir, kapsamı (scope) sınırlanabilir ve tek tek iptal edilebilir — parolaya göre
büyük avantajı budur.

### 6 — OAuth2 client credentials (makine-makine)

Kullanıcı yok, sadece uygulama var. **İki adım:**

```bash
# 1. Token al
curl -s -X POST "https://accounts.spotify.com/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET"
```

```json
{"access_token": "BQD...", "token_type": "Bearer", "expires_in": 3600}
```

```bash
# 2. Token'i kullan
curl -s -H "Authorization: Bearer $TOKEN" "https://api.spotify.com/v1/browse/new-releases"
```

**Junior tuzağı:** token'ı bir kez alıp sonsuza kadar kullanmak. `expires_in` genelde
3600 saniyedir. Pipeline bir saatten uzun sürerse ortasında 401 alırsın.

**Prod'da ne kırılır:** token'ı her istekte yeniden almak da yanlış — token endpoint'inin
kendi rate limit'i vardır. Doğrusu: token'ı sürelİ önbellekte tut, süresi dolmadan
biraz **önce** (örneğin 60 sn marj) yenile. Saat kayması (clock skew) yüzünden marjsız
yenileme ara ara 401 üretir.

### 7 — OAuth2 authorization code (kullanıcı adına)

Kullanıcının **kendi** verisine erişmek gerektiğinde. `curl` tek başına yetmez, çünkü
akışın ortasında insan onayı var:

1. Kullanıcı tarayıcıda yetkilendirme URL'sine gider
2. "İzin ver" der
3. Uygulamanın `redirect_uri`'sine `?code=...` ile döner
4. Uygulama bu `code`'u token'a takas eder (bu adım curl ile yapılabilir)
5. `refresh_token` ile ileride sessizce yenilenir

```bash
curl -s -X POST "https://oauth2.example.com/token" \
  -d "grant_type=authorization_code&code=$CODE&redirect_uri=$REDIRECT&client_id=$ID&client_secret=$SECRET"
```

**PKCE** (Proof Key for Code Exchange) bu akışın mobil/SPA için sertleştirilmiş hâlidir:
istemci bir `code_verifier` üretir, hash'ini önden gönderir. Client secret saklayamayan
istemciler için tasarlandı, bugün **tüm** istemciler için önerilir (RFC 7636 + OAuth 2.1
taslağı).

**Veri mühendisliği açısından kritik:** bu model batch pipeline'a kötü uyar. Refresh
token süresiz değildir, iptal edilebilir, ve dolduğunda pipeline'ın **bir insana ihtiyacı
olur**. Gece 3'te çalışan bir job için bu kabul edilemez. Mümkünse client credentials
ya da service account tercih edilir.

### 8 — OAuth2 device code

Klavyesi olmayan ya da tarayıcı açamayan cihazlar için (TV, CLI). Cihaz bir kod gösterir,
kullanıcı başka bir cihazda o kodu girer, cihaz arka planda token'ı yoklar (polling).
`gh auth login` ve `aws sso login` bu akışı kullanır.

### 9 — JWT / service account

Google Cloud'un makine-makine modeli. Elinde bir **private key** vardır; onunla kısa
ömürlü bir JWT imzalar, JWT'yi access token'a takas edersin.

```
private key ──imzala──> JWT ──takas et──> access token ──> API
```

Elle yapmak zordur (imzalama adımı yüzünden); pratikte SDK kullanılır. Bilinmesi gereken:
**dosya olarak duran bir private key** vardır ve o dosya en kritik sırdır. Repoya sızan
service account JSON'ları, bulut faturası patlamalarının klasik sebebidir.

### 10 — HMAC imzalı istek

İsteğin **içeriği** imzalanır. Sadece kimlik değil, isteğin yolda değiştirilmediği de
kanıtlanır.

- **AWS SigV4:** metot, yol, sorgu, header'lar, gövde hash'i ve zaman damgası kanonik
  bir metne dizilir, türetilmiş anahtarla HMAC-SHA256 alınır. Elle üretmek pratikte
  imkânsızdır — `awscli` ya da `boto3` kullanılır.
- **Last.fm `api_sig`:** parametreler alfabetik sıralanır, `<isim><değer>` olarak
  birleştirilir, sonuna **shared secret** eklenir, MD5 alınır.

Buradaki ayrım, bu projede shared secret'ı `.env`'e koymama kararının gerekçesiydi:

> `api_key` **kim olduğunu** söyler (kimlik).
> `shared_secret` **o olduğunu kanıtlar** (yetki) — ve asla ağa çıkmaz.

Aynı mekanizma ters yönde de kullanılır: Stripe ve Shopify **webhook**'ları HMAC ile
imzalar. Webhook alıcısı imzayı doğrulamazsa, herkes o endpoint'e sahte "ödeme alındı"
gönderebilir.

### 11 — mTLS (karşılıklı TLS)

Sunucu istemciyi de sertifikayla doğrular. Open Banking ve kurumsal entegrasyonlarda yaygın.

```bash
curl -s --cert client.pem --key client.key "https://api.bank.example.com/accounts"
```

Sır bir string değil, bir **dosya çiftidir**. `.env`'e sığmaz; dosya izinleri ve
sertifika **son kullanma tarihi** ayrı bir operasyon konusudur. Sessizce çalışan bir
entegrasyonun bir sabah durmasının klasik sebebi: sertifika süresi doldu.

### 12 — Session cookie

Eski web uygulamaları. Login'e POST atarsın, sunucu `Set-Cookie` döner, sonraki istekleri
o cookie ile yaparsın.

```bash
curl -s -c cookies.txt -d "user=u&pass=p" "https://example.com/login"
curl -s -b cookies.txt "https://example.com/api/data"
```

`-c` yazar (cookie jar), `-b` okur. API için tasarlanmamıştır; CSRF token'ları ve oturum
zaman aşımı yüzünden otomasyonda kırılgandır.

---

## 9. curl yetmediğinde

| Araç | Ne zaman |
|---|---|
| `httpie` | İnsan dostu sözdizimi, JSON'ı renklendirir ve otomatik biçimler |
| **Postman / Insomnia** | OAuth akışlarını arayüzden yürütür, token'ı otomatik yeniler |
| **Bruno** | Postman benzeri ama koleksiyonlar **dosya** olarak durur → git'e girer |
| `.netrc` | Kimlik bilgilerini komuttan tamamen çıkarır (`curl -n`) |
| `jq` | Büyük JSON'da alan keşfi: `curl -s ... \| jq 'keys'` |

**Bruno'nun git avantajı önemli:** Postman koleksiyonları bulutta yaşar ve versiyonlanmaz.
Bir API sözleşmesinin repoda, kodla birlikte versiyonlanması ekip çalışmasında ciddi fark
yaratır.

---

## 10. Barış önce şöyle sandı

| Sandığım | Gerçek |
|---|---|
| `raise_for_status()` yanlış formatı yakalar | Yakalamaz — XML de `200` ile gelir. Status kodu format hakkında hiçbir şey söylemez |
| `JSONDecodeError` mesajı problemi anlatır | Anlatmaz. "char 0" mesajı boş gövdede, HTML'de, XML'de aynıdır |
| Shared secret'ı da `.env`'e koymak lazım | Gerekmez. Bu proje sadece public metodları çağırıyor; kullanılmayan sır sıfır fayda, artı risk |
| `format` query param'ı bir tasarım hatası | Takas. URL'yi kendi kendine yeterli ve cache dostu yapar; karşılığında standart dışıdır |
| PowerShell'de `curl` = curl | Hayır, `Invoke-WebRequest` alias'ı. `curl.exe` yazmak gerekir |

---

## 11. Kontrol listesi — yeni bir API'ye başlarken

- [ ] Auth modeli hangisi? (yukarıdaki 12 maddeden biri)
- [ ] Sır nerede taşınıyor: URL mi, header mı? URL'deyse loglama planı ne?
- [ ] Sır komut geçmişine giriyor mu? Env var'a alındı mı?
- [ ] Token'ın ömrü var mı? Varsa yenileme kimin sorumluluğunda?
- [ ] Varsayılan yanıt formatı ne? JSON'ı açıkça istemek gerekiyor mu?
- [ ] Hata **status kodunda** mı, **gövdede** mi geliyor? (elle bozuk istek atarak dene)
- [ ] Rate limit ne? Header'da kalan kota bildiriliyor mu?
- [ ] Sayfalama (pagination) var mı? Kaç kayıt dönüyor, `limit` tavanı ne?
- [ ] Gerçek payload diske kaydedildi mi? (fixture olacak)
- [ ] Hata payload'ı da kaydedildi mi?

---

## 12. Mülakat

**"Yeni bir API entegrasyonuna nasıl başlarsın?"**
→ *"Kod yazmadan önce `curl` ile elle çağırırım. Amaç dokümantasyonun iddiasını gerçek
payload'la karşılaştırmak — tipler, null'lar ve hata biçimi neredeyse her zaman dokümandan
farklıdır. Hem başarı hem hata cevabını diske kaydederim; ikisi de test fixture'ı olur."*

**"API key'i nerede saklarsın?"**
→ *"Local'de `.env`, repoda `.env.example` ile sözleşmesi. Prod'da environment variable
değil, secret manager — SSM Parameter Store ya da Secrets Manager. Komut satırına asla
yazmam, shell geçmişi düz metin bir dosyadır."*

**"HTTP 200 dönen bir cevap her zaman başarılı mıdır?"**
→ *"Hayır. Status kodu sunucunun isteği işlediğini söyler, doğru veriyi aldığımı değil.
Last.fm bunun ders kitabı örneği: geçersiz API key'de bile 200 döner, hata gövdenin
içindedir. Bu yüzden `raise_for_status()` yeterli bir kontrol değil — gövdeyi de
doğrulamak gerekir."*

**"Bir sır repoya sızarsa ilk hamlen ne olur?"**
→ *"Rotate. Sırrı hemen iptal edip yenisini üretirim. Git geçmişini temizlemek ikinci
adımdır ve tek başına yetersizdir — push edilmişse fork'larda, başkalarının klonlarında
ve platform cache'inde durmaya devam eder. Public repoda otomatik tarayıcılar sırları
dakikalar içinde bulur."*

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **API exploration / spike** | Kod yazmadan önce API'yi elle çağırıp gerçeği öğrenme adımı |
| **content negotiation** | İstemcinin istediği temsili belirtmesi. Standart yolu `Accept` header'ı |
| **capture group** | Regex'te `( )` ile işaretlenen, sonradan geri alınabilen parça |
| **greedy / lazy** | Niceleyicinin mümkün olduğunca çok (`*`) veya az (`*?`) eşleşmesi |
| **PAT** | Personal Access Token — panelden üretilen, kapsamı sınırlı, iptal edilebilir token |
| **scope** | Bir token'ın neye izin verdiğini sınırlayan yetki etiketi |
| **PKCE** | Client secret saklayamayan istemciler için OAuth code akışının sertleştirilmiş hâli |
| **HMAC** | Paylaşılan gizli anahtarla üretilen mesaj imzası; içeriğin değişmediğini kanıtlar |
| **SigV4** | AWS'nin HMAC tabanlı istek imzalama şeması |
| **mTLS** | Karşılıklı TLS — sunucu da istemciyi sertifikayla doğrular |
| **cookie jar** | curl'ün cookie'leri sakladığı dosya (`-c` yazar, `-b` okur) |
| **clock skew** | İstemci ve sunucu saatleri arasındaki kayma; imzalı ve süreli token'larda hata sebebi |

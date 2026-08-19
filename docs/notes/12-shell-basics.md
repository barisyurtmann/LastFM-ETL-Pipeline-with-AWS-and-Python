# 12 — Shell temelleri: bash, Git Bash, PowerShell

> Adım 1.4 · 2026-08-11

Bu not, projede yazdığımız komutların **her parçasını** açıklar. Amaç komut ezberlemek
değil, bir komut satırına bakınca onu **okuyabilmek**.

Veri mühendisliğinde shell kaçınılmaz: CI pipeline'ları, Dockerfile'lar, cron job'ları,
Makefile'lar — hepsi shell komutudur. Python bilip shell bilmemek, sürekli takılınan
bir noktadır.

> **Kısa cevap** — Bir komut satırındaki her sembol ne iş yapıyor ve nerede sessizce kırılır?
>
> 1. Exit code 0 başarıdır; cron, CI ve Airflow log'daki "ERROR" kelimesini değil yalnızca bu sayıyı okur.
> 2. `source` olmadan .env yüklenmez; yüklense de sadece shell değişkeni olur, Python alt süreci göremez — `set -a` şart.
> 3. `source .env` dosyayı bash script olarak çalıştırır (`$(...)` dahil); pydantic-settings parse eder, çalıştırmaz.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

---

## 1. Hangi shell'i kullanıyorum

Windows'ta aynı anda üç farklı shell bulunur ve **komutları farklıdır**:

| Shell | Nasıl anlarsın | Dili |
|---|---|---|
| **Git Bash** (MINGW64) | Prompt: `byurtman@otomasyon MINGW64 ~/Desktop/... $` | bash |
| **PowerShell** | Prompt: `PS C:\Users\byurtman>` | PowerShell |
| **cmd.exe** | Prompt: `C:\Users\byurtman>` | batch |

Bu projede **Git Bash** kullanılıyor. Git for Windows ile birlikte gelir ve Windows
üzerinde bir bash ortamı sağlar — yani Linux/macOS komutları çalışır. Avantajı: sunucuda,
Docker içinde ve CI'da yazacağın komutlarla **aynı** dili kullanmış olursun.

> **Kural: bir komutu kopyalamadan önce hangi shell'de olduğunu bil.** `ls` Git Bash'te
> çalışır, cmd'de çalışmaz. `Get-Content` PowerShell'de çalışır, bash'te çalışmaz.

---

## 2. Bir komutun anatomisi

```bash
curl -s "http://example.com/api" > out.json
└┬─┘ └┬┘ └────────┬────────────┘ └──┬───┘
komut bayrak    argüman        yönlendirme
```

| Parça | Nedir |
|---|---|
| **komut** | Çalıştırılacak program (`curl`, `ls`, `grep`) |
| **bayrak** (flag/option) | Davranışı değiştirir. Kısa: `-s`. Uzun: `--silent` |
| **argüman** | Komutun üzerinde çalışacağı şey (dosya, URL) |

Kısa bayraklar birleştirilebilir: `ls -l -a` = `ls -la`.

Uzun bayrak neden var: `-s` altı ay sonra hatırlanmaz, `--silent` okunur. Script'lerde
uzun, terminalde kısa yazmak yaygın bir alışkanlıktır.

---

## 3. Operatörler — komutları birbirine bağlayanlar

Bu bölüm projede kafa karıştıran her sembolü kapsar.

### `\` — satır devamı

```bash
curl -s "http://example.com" \
  | python -m json.tool \
  > out.json
```

Ters bölü, satır sonundaki yeni satır karakterini **iptal eder**: "bu komut bitmedi,
alt satırdan devam ediyor" demektir. Yukarıdaki üç satır, shell için **tek bir komuttur**.

Neden kullanılır: uzun komutları okunabilir tutmak.

> **Tuzak:** `\` işaretinden **sonra hiçbir şey olamaz** — tek bir boşluk bile.
> Boşluk varsa `\` boşluğu kaçırır, satır sonu iptal edilmez, komut yarıda kesilir.
> Bu hatayı gözle görmek neredeyse imkânsızdır.

Komutu tek satıra yazacaksan `\` işaretlerini **sil**, satır sonlarını birleştir:

```bash
curl -s "http://example.com" | python -m json.tool > out.json
```

### `|` — pipe (boru)

Sol komutun **çıktısını**, sağ komutun **girdisi** yapar.

```bash
curl -s "URL" | python -m json.tool
```

curl indirir, ekrana yazmak yerine python'a verir; python biçimlendirir.

Bu Unix felsefesinin merkezindeki fikirdir: **her program tek bir işi iyi yapar,
programlar birbirine bağlanır.** curl'ün JSON biçimlendirme özelliği yoktur ve olmasına
gerek de yoktur.

Zincir uzayabilir:

```bash
cat dosya.json | grep "name" | head -5
```

### `>` ve `>>` — yönlendirme

```bash
komut > dosya    # dosyayi SIFIRLAYIP yazar
komut >> dosya   # dosyanin SONUNA ekler
```

> **Tuzak:** `>` uyarı vermeden dosyanın içeriğini siler. Dolu bir dosyaya yanlışlıkla
> `>` yazmak, geri dönüşü olmayan bir işlemdir.

### `<` — girdiyi dosyadan almak

```bash
python -m json.tool < girdi.json
```

Az kullanılır çünkü çoğu komut dosya adını argüman olarak zaten kabul eder.

### `/dev/null` — çöp kutusu

```bash
python -m json.tool dosya.json > /dev/null
```

`/dev/null` Unix'te özel bir aygıttır: kendisine yazılan **her şeyi yutar**. Okumaya
çalışırsan hemen "dosya sonu" döner.

Neden kullandık: `json.tool` dosyayı doğrularken içeriğini de ekrana basar. Bize gereken
"geçerli mi" cevabıydı, 32 KB JSON değil. Çıktıyı çöpe atıp yalnızca **başarılı olup
olmadığına** baktık.

### `2>` — hata çıktısını yönlendirmek

Her komutun **iki** çıkış kanalı vardır:

| Kanal | Numara | Ne taşır |
|---|---|---|
| stdout | `1` | Normal çıktı |
| stderr | `2` | Hata mesajları |

```bash
komut > out.txt 2> hata.txt    # ayri dosyalara
komut > out.txt 2>&1           # ikisini ayni dosyaya
komut 2> /dev/null             # hatalari sustur
```

Bu ayrım kritik: `curl -s "URL" > out.json` yazdığında hata mesajı dosyaya **karışmaz**,
ekranda kalır. Aksi hâlde JSON dosyanın içine hata metni sızardı.

### `;` — komutları sırayla çalıştır

```bash
set -a; source .env; set +a
```

Üç ayrı komut, soldan sağa. **Sonuca bakmaz** — biri patlasa da diğerleri çalışır.

### `&&` — öncekiler başarılıysa çalıştır

```bash
python -m json.tool dosya.json > /dev/null && echo "GECERLI JSON"
```

`echo` **yalnızca** `json.tool` başarılı olursa çalışır. Dosya bozuksa hiçbir şey
yazılmaz.

### `||` — öncekiler başarısızsa çalıştır

```bash
grep -rn "api_key" tests/ || echo "TEMIZ: api_key gecmiyor"
```

`grep` bir şey **bulamazsa** başarısız sayılır, `echo` çalışır. Bulursa `echo`
çalışmaz — eşleşen satırlar ekrana basılır.

Yani bu satırın anlamı: *"tests/ altında api_key ara; bulursan göster, bulamazsan
TEMIZ yaz."* Tek satırda hem arama hem raporlama.

`&&` ve `||` birlikte, üçlü koşul gibi kullanılır:

```bash
komut && echo "BASARILI" || echo "BASARISIZ"
```

---

## 4. Exit code — `&&` ve `||` neye bakıyor

Her komut bittiğinde geriye bir **sayı** bırakır:

| Değer | Anlamı |
|---|---|
| `0` | Başarılı |
| `0` dışı | Başarısız (hangi hata olduğunu komut belirler) |

Sezgiye ters: **sıfır iyidir.** Sebebi, başarısızlığın birçok türü olması — 1, 2, 127
farklı hataları anlatabilir; başarının ise tek bir türü vardır.

Son komutun exit code'unu görmek:

```bash
echo $?
```

`grep` özelinde:

| Exit code | Anlamı |
|---|---|
| `0` | En az bir eşleşme buldu |
| `1` | Hiç eşleşme yok |
| `2` | Gerçek hata (dosya yok, izin yok) |

Bu yüzden `grep ... || echo "TEMIZ"` çalışıyor: eşleşme yoksa `1` döner, `||` devreye girer.

> **Bu kavram bu projede tekrar karşımıza çıkacak.** ROADMAP 6.5 "exit code sözleşmesi"
> diyor ve `PROJECT_CONTEXT.md` §1'de geçmiş projenin hatası olarak *"pipeline patladığında
> `echo $?` sıfırdan farklı olmalı"* yazıyor. Cron, CI ve Airflow bir işin başarılı olup
> olmadığını **yalnızca** exit code'dan anlar — log'daki "ERROR" kelimesini okumazlar.

---

## 5. Değişkenler, `export` ve `source`

### Değişken tanımlama ve kullanma

```bash
KEY=abc123        # tanimla - esittin etrafinda BOSLUK OLAMAZ
echo $KEY         # kullan  - basina $ gelir
echo "${KEY}"     # suslu parantez: sinirlari netlestirir
```

`KEY = abc123` (boşluklu) **çalışmaz** — bash bunu "KEY adlı komutu çalıştır" diye okur.

`${KEY}` ne zaman gerekli: `$KEYS` ile `${KEY}S` farklıdır. İlki `KEYS` değişkenini arar.

### Shell değişkeni ↔ ortam değişkeni

```bash
X=5           # shell degiskeni  - sadece bu shell gorur
export X=5    # ortam degiskeni  - alt sureclere de gecer
```

`curl`, `python`, `uv` senin shell'inden ayrı **alt süreçlerdir**. Shell değişkenini
göremezler; yalnızca ortam değişkenini görürler.

### Ama bir incelik var

```bash
curl -s "...&api_key=$LASTFM_API_KEY&format=json"
```

Burada `$LASTFM_API_KEY`'i genişleten **bash'in kendisi**, curl çalışmadan önce. Yani
curl'e zaten hazır bir metin gider — export gerekmez.

Export şurada gerekir:

```bash
uv run python -c "import os; print(os.environ['LASTFM_API_KEY'])"
```

Python değeri **kendi ortamından** okuyor. Export edilmemişse `KeyError` alır.

| Durum | Export gerekli mi |
|---|---|
| `$VAR` doğrudan komut satırında geçiyor | Hayır — bash genişletir |
| Alt süreç `os.environ` / `getenv` ile okuyor | **Evet** |

### `source` ne yapar

```bash
source .env      # veya kisa hali:  . .env
```

Dosyayı **mevcut shell'de** çalıştırır. `bash .env` yazsaydın dosya bir **alt shell'de**
çalışırdı ve tanımlanan değişkenler o alt shell kapanınca kaybolurdu.

Evet — buradaki `.env`, 1.1'de **senin oluşturduğun** dosya. İçinde tek satır var:
`LASTFM_API_KEY=...`. `source` onu okuyup değişkeni bu oturuma tanımlar.

> **`source`'un gerçek tehlikesi:** dosyayı bir **bash script'i olarak çalıştırır.**
> İçinde ne varsa çalışır — komut ikamesi (`$(...)`) dahil. `.env` dosyalarına
> güvenmek zorunda kalırsın.
> `python-dotenv` ve `pydantic-settings` bunu yapmaz: dosyayı **parse eder**, çalıştırmaz.
> İkincil sonucu: `source` kullanacaksan `.env` bash sözdizimine uymalı —
> `KEY=iki kelime` patlar, `KEY="iki kelime"` çalışır.

### `set -a` / `set +a`

`set`, shell'in davranış anahtarlarını değiştirir. `-a` (`allexport`) açıkken
**tanımlanan her değişken otomatik export edilir**.

```bash
set -a        # anahtari AC
source .env   # buradaki her degisken otomatik export edilir
set +a        # anahtari KAPAT
```

Bash'te `-` açar, `+` kapatır. Sezgiye ters ama kural bu.

`source .env` tek başına yazılsaydı değişkenler yalnızca shell değişkeni olurdu ve
Python onları göremezdi. Alternatifi her satıra tek tek `export` yazmaktır — `set -a`
bunu toplu yapar.

**`set +a` neden şart:** açık kalırsa o oturumda tanımladığın **her** değişken export
edilir. Geçici bir `tmp=/foo` bile tüm alt süreçlere sızar. Bir anahtarı açtığın kadar
dar tutmak genel bir disiplindir.

### Diğer faydalı `set` seçenekleri

Script yazarken standart başlangıç satırı:

```bash
set -euo pipefail
```

| Bayrak | Ne yapar |
|---|---|
| `-e` | Bir komut hata verirse script'i **durdur** |
| `-u` | Tanımsız değişken kullanılırsa hata ver |
| `-o pipefail` | Pipe zincirinde **herhangi biri** patlarsa zinciri başarısız say |

Bunlar olmadan bash sessizce devam eder — "sessiz başarı" hatasının shell versiyonu.

---

## 6. Tırnaklar: `"` ve `'` farkı

| Tırnak | Değişken genişler mi | Ne zaman |
|---|---|---|
| `"çift"` | **Evet** | İçinde `$VAR` varsa |
| `'tek'` | Hayır — metin aynen kalır | Ham metin isteniyorsa |
| tırnaksız | Genişler, **ama boşluk ve özel karakterler böler** | Kısa ve güvenli komutlarda |

```bash
KEY=abc
echo "$KEY"    # abc
echo '$KEY'    # $KEY
```

**URL'ler neden mutlaka tırnak içinde:** `&`, `?`, `*` karakterleri shell için özel
anlam taşır. `&` bash'te "arka planda çalıştır" demektir — tırnaksız bir URL'de komut
`&` işaretinden bölünür ve isteğin yarısı kaybolur.

Bu hata **sinsi**: komut çalışır, cevap gelir, ama parametrelerin bir kısmı yoktur.

---

> **Döngüler bu notta değil.** `for` / `while` / `until`, hangi formun ne zaman
> seçileceği, `break`/`continue`, PowerShell karşılıkları ve paralel döngü
> → [not 16](16-shell-loops-and-measurement.md). Gerekçe: döngü sözdizimi tek başına
> yarım bir bilgi; asıl öğrenilecek olan **hangi formu neden seçtiğin** ve o karar
> ölçüm bağlamından ayrılmıyor.

---

## 7. Kullandığımız komutlar

### `ls` — listele

```bash
ls -la tests/fixtures/lastfm/
```

| Bayrak | Ne yapar |
|---|---|
| `-l` | Uzun format: izinler, sahip, boyut, tarih |
| `-a` | Gizli dosyaları da göster (`.` ile başlayanlar — `.env` gibi) |
| `-h` | Boyutu okunur yaz (`31876` yerine `31K`) |

Çıktının okunması:

```
-rw-r--r-- 1 byurtman 1049089 31876 Aug 11 14:54 chart_gettoptracks_success.json
└────┬───┘ │ └───┬──┘         └─┬─┘ └────┬────┘ └──────────────┬─────────────┘
  izinler  │   sahip          byte     tarih                  ad
        link sayisi
```

İlk karakter türü söyler: `-` normal dosya, `d` klasör, `l` sembolik link.

### `mkdir -p` — klasör oluştur

```bash
mkdir -p tests/fixtures/lastfm
```

`-p` iki iş yapar:

1. **Ara klasörleri de oluşturur** — `tests/` ve `tests/fixtures/` yoksa onları da açar
2. **Klasör zaten varsa hata vermez**

İkincisi script'lerde kritiktir: `-p` olmadan ikinci çalıştırmada script patlar.
Bu, **idempotency**'nin en basit örneğidir — aynı komutu iki kez çalıştırmak, bir kez
çalıştırmakla aynı sonucu verir. Aynı fikri Adım 4.5 ve 5.7'de dosya yazarken göreceğiz.

### `grep` — metin ara

```bash
grep -rn "api_key" tests/
```

| Bayrak | Ne yapar |
|---|---|
| `-r` | Klasörün içine **özyinelemeli** iner (recursive) |
| `-n` | Eşleşen **satır numarasını** yazar |
| `-i` | Büyük/küçük harf ayrımı yapmaz |
| `-l` | Sadece dosya adlarını yazar, satırları değil |
| `-v` | Eşleşme**yen** satırları göster (tersine çevirir) |
| `-c` | Eşleşen **satır** sayısını yaz (satırların kendisini değil) |

Adı "**g**lobally search for a **r**egular **e**xpression and **p**rint" ifadesinden gelir.

**`-c` ne sayar:** eşleşen **satır** sayısını, eşleşme sayısını değil. Bir satırda kelime
üç kez geçse bile `1` sayılır.

```bash
grep -c "name" dosya.json        # kac SATIRDA gecti
grep -o "name" dosya.json | wc -l   # kac KEZ gecti
```

`-o` yalnızca eşleşen parçaları basar (her biri ayrı satırda), `wc -l` satırları sayar.
Bu ayrım, "kaç kayıt var" diye sayarken yanlış sonuç almanın klasik sebebidir.

Bizim kullanımımız bir **güvenlik kontrolüydü**: fixture dosyalarına API key sızmış mı?
Dosyalar git'e girecek ve bir kez sızan sır geçmişte kalır.

### `echo` — ekrana yaz

```bash
echo "TEMIZ"
echo $?          # son exit code
echo "$KEY"      # degisken degeri
```

Script'lerde ve `&&` / `||` zincirlerinde durum bildirmek için kullanılır.

### `cat`, `head`, `tail` — dosya içeriği

```bash
cat dosya.json           # tamamini yaz
head -20 dosya.json      # ilk 20 satir
tail -20 dosya.json      # son 20 satir
tail -f app.log          # dosyayi CANLI izle - log takibinde standart
```

`tail -f` veri mühendisliğinde çok kullanılır: çalışan bir pipeline'ın log'unu anlık izlemek.

---

## 8. bash ↔ PowerShell sözlüğü

Aynı işi iki shell'de yapmak gerektiğinde:

| İş | bash / Git Bash | PowerShell |
|---|---|---|
| Dosya listele | `ls -la` | `Get-ChildItem` (`ls` alias'tır ama farklıdır) |
| Dosya içeriği | `cat dosya` | `Get-Content dosya` |
| Metin ara | `grep "x" dosya` | `Select-String "x" dosya` |
| Klasör oluştur | `mkdir -p a/b` | `New-Item -ItemType Directory -Force a/b` |
| Ortam değişkeni | `$VAR` | `$env:VAR` |
| Değişken ata | `X=5` | `$X = 5` |
| Satır devamı | `\` | `` ` `` (backtick) |
| Çöp kutusu | `/dev/null` | `$null` |
| Son exit code | `$?` (sayı) | `$LASTEXITCODE` (sayı) / `$?` (mantıksal) |
| curl | `curl` (gerçek curl) | **`curl.exe`** — `curl` alias'ı `Invoke-WebRequest`'tir |

> **PowerShell'in en sinsi tuzağı:** `>` yönlendirmesi. PowerShell 5.1'de varsayılan
> kodlama **UTF-16 LE**'dir. `curl.exe ... > dosya.json` yazarsan dosya UTF-16 olur ve
> `json.tool` onu okuyamaz. Git Bash'te bu sorun yoktur — bu projede Git Bash tercih
> etmenin pratik sebeplerinden biri.

---

## 9. Windows'a özgü notlar

### `python` mu `py` mi

Windows'ta Python launcher `py` komutunu kurar. `python` PATH'te olmayabilir ya da
Microsoft Store'un sahte kısayoluna gidebilir.

```bash
py -m json.tool dosya.json      # Windows launcher
python -m json.tool dosya.json  # PATH'teki python
uv run python -m json.tool ...  # projenin .venv'indeki python  <- en guvenilir
```

Bu projede üçüncüsü tercih edilmeli: hangi Python'ın çalıştığı belirsiz kalmaz.

### `-m` bayrağı ne demek

```bash
python -m json.tool
```

"Şu **modülü** script olarak çalıştır" demektir. `json.tool` bir dosya yolu değil,
Python'ın standart kütüphanesindeki bir modüldür. `-m` sayesinde modülün nerede kurulu
olduğunu bilmen gerekmez.

Aynı desen: `python -m pytest`, `python -m pip install`, `python -m venv`.

### Yol ayırıcı

Git Bash `/` kullanır ve Windows yollarını çevirir: `C:\Users\x` → `/c/Users/x`.
Komutlarda `/` yazman yeterlidir.

---

## 10. Barış önce şöyle sandı

| Sandığım | Gerçek |
|---|---|
| `\` bir kaçış karakteri, metinle ilgili | Satır sonunu iptal eder: "komut alt satırda devam ediyor" |
| `set -a` olmadan `.env` yüklenmez | Yüklenir — ama sadece shell değişkeni olur. Alt süreçler (Python) göremez |
| `.env` özel bir dosya, sistem otomatik okur | Hayır. Sıradan bir metin dosyası; onu okuyan bir şey **olmak zorunda** (`source`, `python-dotenv`, `pydantic-settings`) |
| `grep` sadece arama yapar | Aynı zamanda **exit code** döndürür — `\|\|` ile birleşince koşullu mantık kurar |
| Exit code'da `1` başarı olurdu | Tersi: `0` başarı. Başarısızlığın çok türü var, başarının bir |
| `>` dosyaya ekler | **Sıfırlayıp yazar.** Eklemek `>>` |

---

## 11. Sık yapılan hatalar

| Hata | Sonuç |
|---|---|
| `\` sonrasında boşluk bırakmak | Satır devamı çalışmaz, komut yarıda kesilir — gözle görülmez |
| `KEY = value` (boşluklu atama) | `KEY: command not found` |
| URL'yi tırnaksız yazmak | `&` komutu böler, parametrelerin bir kısmı kaybolur |
| `>` yerine `>>` demek isterken `>` yazmak | Dosya içeriği uyarısız silinir |
| PowerShell'de `curl` yazmak | `Invoke-WebRequest` çalışır, bayraklar tanınmaz |
| PowerShell'de `>` ile dosya yazmak | UTF-16 kodlama, dosya bozulur |
| `set -a` açık bırakmak | Sonraki tüm değişkenler alt süreçlere sızar |
| Script'te `set -euo pipefail` yazmamak | Hata sessizce yutulur, script "başarılı" biter |

---

## 12. Mülakat

**"Bir script'in başarılı olup olmadığını nasıl anlarsın?"**
→ *"Exit code'dan. `0` başarı, sıfır dışı başarısızlık. Cron, CI ve orchestrator'lar
yalnızca buna bakar — log'daki 'ERROR' kelimesini okumazlar. Bu yüzden pipeline'ın
hata durumunda sıfır dışı bir kodla çıkması, loglama kadar önemlidir."*

**"`&&` ile `;` arasındaki fark ne?"**
→ *"`;` komutları sırayla çalıştırır, sonuca bakmaz. `&&` yalnızca öncekiler başarılıysa
devam eder. CI script'lerinde `;` kullanmak tehlikelidir: ilk adım patlasa bile sonrakiler
çalışır ve script başarılı görünebilir."*

**"`.env` dosyası nasıl yükleniyor?"**
→ *"Kendiliğinden yüklenmiyor. Onu okuyan bir şey olmak zorunda: shell'de `source`,
Python'da `python-dotenv` ya da `pydantic-settings`. `source` dosyayı bash script'i olarak
**çalıştırır**, kütüphaneler ise **parse eder** — güvenlik açısından ikincisi tercih
edilir."*

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **shell** | Komutları yorumlayıp çalıştıran program (bash, PowerShell, zsh) |
| **flag / option** | Komutun davranışını değiştiren parametre (`-r`, `--recursive`) |
| **pipe** (`\|`) | Bir komutun çıktısını diğerinin girdisine bağlamak |
| **stdout / stderr** | Normal çıktı (1) ve hata çıktısı (2) kanalları |
| **exit code** | Komutun bıraktığı sonuç sayısı. `0` = başarı |
| **redirection** (`>`, `>>`) | Çıktıyı ekran yerine dosyaya yönlendirmek |
| **`/dev/null`** | Yazılanı yutan özel aygıt; çıktıyı atmak için |
| **environment variable** | Alt süreçlere miras kalan değişken (`export` ile) |
| **subprocess** | Shell'in başlattığı ayrı program (curl, python) |
| **source** (`.`) | Dosyayı mevcut shell'de çalıştırmak, alt shell açmadan |
| **idempotent** | Aynı komutu iki kez çalıştırmanın bir kez çalıştırmakla aynı sonucu vermesi |
| **recursive** (`-r`) | Alt klasörlere de inmek |

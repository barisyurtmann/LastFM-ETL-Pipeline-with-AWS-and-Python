# 01 — Git temelleri ve `.gitignore`

> Adım 0.1 · 2026-08-07 — inline yorum tuzağı ve `check-ignore` bölümü 0.4'te eklendi,
> negation/`-v` tuzağı 0.5'te eklendi (2026-08-10)

## Neden `.gitignore` ilk iş olarak yazılır

Yaygın olarak anlatılan gerekçe **yanlıştır**: "`.gitignore` commit'lenmeden koruma
sağlamaz" doğru değil. Git, `.gitignore`'u **çalışma dizinindeki dosya** olarak okur.
Diske yazdığın an yürürlüğe girer, commit'lenmiş olması gerekmez.

Gerçek gerekçe iki tane:

**1. Git geçmişi kalıcıdır.**
`.gitignore` sadece **untracked** dosyaları etkiler. Bir dosya bir kez `git add` edildiyse,
sonradan `.gitignore`'a yazsan da git onu takip etmeye devam eder — `git rm --cached`
demen gerekir. Ve takipten çıkarsan bile dosya **commit geçmişinde durur**;
`git log -p` ile herkes okur.

**2. Sır bir kez push'landıysa o sır yanmıştır.**
Temizlemek için `git filter-repo` / BFG ile geçmişi yeniden yazmak, force-push atmak ve
repoyu klonlamış herkesin repoyu silip yeniden klonlaması gerekir. Sektör pratiği:
geçmişi temizlemeye uğraşma, **anahtarı iptal edip yenisini al (rotate).**

## `.gitignore` kalıp syntax'ı

Slash'in yeri her şeyi değiştirir:

| Kalıp | Ne eşleşir |
|---|---|
| `raw` | Her seviyedeki `raw` adlı **dosya ve klasör** |
| `raw/` | Her seviyedeki `raw` **klasörü** |
| `/raw/` | Sadece **repo kökündeki** `raw` klasörü |

**Kural: ne kadar dar yazabiliyorsan o kadar dar yaz.**
Ignore etmek geri alınabilir, yanlışlıkla ignore edilmiş dosyayı fark etmek zordur.

### Somut tuzak

`raw` (slash'siz) yazarsan, ileride `src/lastfm_etl/raw/` diye bir modül klasörü açtığında
git onu **sessizce yok sayar**. `git add .` yaparsın, `git status` temiz görünür,
push'larsın, CI'da `ModuleNotFoundError` alırsın. Bu "sessiz başarısızlık"ın git versiyonu.

### Diğer syntax parçaları

| Parça | Anlamı |
|---|---|
| `*.py[cod]` | Glob character class — `.pyc`, `.pyo`, `.pyd` üçünü birden yakalar |
| `!kalıp` | Negation: "bunu ignore'dan muaf tut" |
| `**` | Herhangi sayıda ara klasör (`data/**` = data içindeki her şey) |

## Inline yorum tuzağı

**Barış önce şöyle sandı:** `.gitignore` de kod gibidir, satır sonuna yorum yazılabilir.

```gitignore
__pycache__/          # compiled bytecode, regenerated on every run
.venv/                # machine-specific
```

**Aslında:** `.gitignore` **satır sonu (inline) yorumu desteklemez.** Git yalnızca `#`
ile **başlayan** satırı yorum sayar. Yukarıdaki satırlarda pattern, `#` dahil satırın
tamamıdır:

```
__pycache__/          # compiled bytecode, regenerated on every run
```

Böyle bir isimde dosya olmadığı için **hiçbir şey ignore edilmez.** Hata mesajı yok,
uyarı yok — dosya sessizce çalışmaz.

Doğrusu, yorumu kendi satırına almak:

```gitignore
# compiled bytecode, regenerated on every run
__pycache__/
```

### Bu tuzak 0.4'e kadar neden fark edilmedi

0.1'de `git check-ignore -v` ile doğrulama yapıldı — ama `.env` ve `data/` üzerinden.
O iki satırda inline yorum yoktu, dolayısıyla test yeşil geçti. Ortam kurulup `.venv/`
diske düştüğünde `git status` üç kirli girdi gösterdi:

```
?? .venv/
?? lastfm_etl.egg-info/
?? src/            <- icindeki __pycache__ yuzunden
```

**Genel ders — bu, notun sonundaki "cache vs gerçek" dersinin kardeşi:**
doğrulamayı **örnek** üzerinden yaptın, **kalıp** üzerinden değil. İki dosya test edip
"ignore çalışıyor" sonucuna varmak, test edilmemiş satırların çalıştığını **varsaymak**tır.
Doğru test: her pattern için en az bir yol.

### İlgili syntax detayları

| Durum | Davranış |
|---|---|
| Satır sonundaki boşluklar | Git tarafından yok sayılır (`\ ` ile escape edilmedikçe) |
| `#` ile **başlayan** satır | Yorum |
| `#` satırın **ortasında** | Pattern'ın parçası — yorum değil |
| Adı gerçekten `#` ile başlayan dosya | `\#dosya` diye escape et |
| Adı gerçekten `!` ile başlayan dosya | `\!dosya` diye escape et |
| Boş satır | Hiçbir şeyle eşleşmez; sadece okunabilirlik için |

## Negation (`!`) ve sıra

Git `.gitignore`'u yukarıdan aşağı okur; **en son eşleşen satır kazanır.**
`.gitignore`'da sırayı önemli kılan tek mekanizma budur.

```gitignore
.env            # eşleşti → ignore
.env.*          # .env.example de eşleşti → ignore
!.env.example   # tekrar eşleşti, negation → ignore DEĞİL
```

Sırayı bozarsan çalışmaz:

```gitignore
!.env.example   # muaf tuttun
.env.*          # sonra tekrar ignore ettin — son eşleşen bu, dosya ignore'lu
```

### Negation'ın büyük tuzağı

Ignore edilmiş bir **klasörün içindeki** dosyayı `!` ile geri getiremezsin:

```gitignore
/data/
!/data/sample.json    # ÇALIŞMAZ
```

Git `/data/`'yı komple ignore ettiği için içine hiç girmez (performans optimizasyonu).
Bakmadığı klasörde negation'ı da göremez. Çözüm: ya klasörü değil içeriğini ignore et
(`/data/**`), ya da dosyayı başka yere koy.

## `.env` ve `.env.example`

`.env` sırları tutar, asla commit'lenmez. Ama o zaman repoyu klonlayan biri hangi
değişkenleri doldurması gerektiğini nereden bilecek?

Bu yüzden aynı yapıya sahip, **değerleri boş** bir kardeş dosya commit'lenir:

```
LASTFM_API_KEY=
LASTFM_BASE_URL=http://ws.audioscrobbler.com/2.0/
LOG_LEVEL=INFO
```

Değerler değil, **anahtarlar** sözleşmedir. Yeni gelen `cp .env.example .env` yapar.

Yaygın bir konvansiyon, resmî standart değil (`.env.sample`, `.env.template` de görülür).

**Prod'da ne kırılır:** `.env.example`'ı güncellemeyi unutmak. Kodda yeni bir
`AWS_REGION` kullanmaya başlarsın, example'a eklemezsin, üç ay sonra deploy eden kişi
`KeyError` alır. Adım 2'de Pydantic Settings bunu yapısal olarak çözecek — eksik değişken
program **başlarken** patlayacak, ortasında değil.

## Neyi ignore ederiz — tek cümlelik kural

**Türetilebilen hiçbir şey git'e girmez.** Git'in işi kaynağı versiyonlamak.

| Dosya | Bu ne? |
|---|---|
| `__pycache__/` | Python bir `.py`'yi import ederken ürettiği bytecode. Silersen ilk çalıştırmada geri gelir. |
| `*.py[cod]` | O bytecode dosyalarının kendisi. `.pyd` = Windows'ta derlenmiş uzantı. |
| `*.egg-info/` | `pip install -e .` sırasında oluşan paket metadata'sı. Kaynağı `pyproject.toml`. |
| `.venv/` | Sanal ortam. Yüzlerce MB ve **makineye özel** (mutlak yollar içerir), başkası kullanamaz. |
| `.pytest_cache/` | pytest'in "son patlayan testler" hafızası (`--lf` için). |
| `.mypy_cache/` | mypy'ın tip kontrolü sonuçları — ikinci çalıştırma hızlı olsun diye. |
| `.ruff_cache/` | Aynı mantık, ruff linter için. |
| `.coverage` | Test kapsama verisi. SQLite binary — git'te diff'i okunamaz. |
| `.DS_Store` | macOS Finder'ın her klasöre bıraktığı görünmez ayar dosyası. |
| `/data/` | Veri. Git kodu versiyonlar, veriyi değil. |

**Mülakat cevabı:** "`.gitignore`'a ne koyarsın?" → *"Türetilmiş çıktıları ve sırları.
Kaynaktan üretilebilen hiçbir şeyin versiyonlanmasına gerek yok, sırların ise
versiyonlanmaması gerekir."*

## Editör klasörleri (`.idea/`, `.vscode/`)

Bu repoda **kasıtlı olarak yok**. Bu bir görüş, evrensel standart değil: editör tercihi
repoya değil sana aittir. Global gitignore'a koy:

```bash
git config --global core.excludesfile ~/.gitignore_global
```

Karşı görüş: `.vscode/settings.json`'ı takım standardı olarak commit'leyen ekipler var.

## `git check-ignore` — doğrulama komutu

`.gitignore` yazmak yarısı; **yazdığının çalıştığını kanıtlamak** diğer yarısı.
`.gitignore`'ın hata mesajı yoktur — yanlış yazılmış bir satır patlamaz, sadece
hiçbir şey yapmaz. Bu yüzden doğrulama isteğe bağlı bir titizlik değil, adımın parçası.

### Ne zaman çalıştırılır

| An | Neden |
|---|---|
| `.gitignore`'a her yeni satır eklendiğinde | Yeni satır test edilmemiş satırdır |
| Yeni bir araç projeye girdiğinde (venv, pytest, mypy, ruff, Docker) | Her araç kendi çöpünü üretir |
| `git status`'ta beklemediğin bir şey göründüğünde | Teşhis aracı |
| Bir dosya `git status`'ta **görünmesi gerekirken görünmediğinde** | Asıl tehlikeli yön — sessizce ignore'lanan kaynak dosya |
| İlk commit'ten önce | En ucuz an |

### Nasıl yazılır

```bash
git check-ignore -v <path> [<path> ...]
```

Yollar diskte var olmak **zorunda değil** — git string üzerinden pattern eşleştirir.
Yani `.venv/` daha oluşmadan da test edebilirsin. (Tek istisna aşağıdaki trailing-slash
kuralı.)

### Çıktı nasıl okunur

Çıktı formatı — ayraçlar önemli, aralarındaki **TAB**'a dikkat:

```
<kaynak>:<satır no>:<pattern>	<sorulan yol>
```

```
.gitignore:11:.venv/	.venv/pyvenv.cfg
└── kaynak    └── pattern   └── senin sorduğun yol
      └── satır no
```

Okunuşu: *".venv/pyvenv.cfg yolu, `.gitignore` dosyasının 11. satırındaki `.venv/`
pattern'ı yüzünden ignore ediliyor."*

**Püf noktası:** en değerli sütun **satır numarası**. Ignore'ın hangi satırdan geldiğini
söyler — birden fazla pattern aynı yolu yakalayabilir ve `!` negation'ları yüzünden
**son eşleşen kazanır**. `check-ignore` sana kazananı gösterir, hepsini değil.

### En sık yapılan yanlış okuma

**Çıktı yoksa "sorun yok" demek değildir — "ignore edilmiyor" demektir.**

`check-ignore` sadece **eşleşen** yolları basar. Beş yol sorup üç satır çıktı aldıysan,
iki yol ignore edilmiyor demektir ve hangileri olduğunu göz kararı bulman gerekir.
Bunu `-n` çözer:

```bash
git check-ignore -v -n .venv/pyvenv.cfg src/lastfm_etl/__init__.py
```

```
.gitignore:11:.venv/	.venv/pyvenv.cfg
::	src/lastfm_etl/__init__.py
```

`::` = boş kaynak, boş satır no, boş pattern → **eşleşme yok**. Artık hangi yolun
eşleşmediği tahmin değil, çıktıda yazıyor. Toplu doğrulamada `-n` her zaman kullanılmalı.

### Diğer bayraklar

| Bayrak | Ne yapar | Ne zaman |
|---|---|---|
| `-v` | Eşleşen kaynağı/satırı/pattern'ı göster | Neredeyse her zaman |
| `-n` | Eşleşmeyenleri de listele (`-v` ile) | Birden fazla yol sorarken |
| `-q` | Çıktı basma, sadece exit code | Script ve CI |
| `--no-index` | Index'i yok say, sadece pattern'a bak | Aşağıdaki tracked tuzağı |
| `--stdin` | Yolları satır satır stdin'den oku | Uzun listeler |

Exit code'lar:

| Kod | Anlamı |
|---|---|
| 0 | En az bir yol ignore'lu |
| 1 | Hiçbiri ignore'lu değil |
| 128 | Hata (bozuk repo, geçersiz argüman) |

> **Bu tablo `-v` ile geçerli değildir.** Sebebi Tuzak 3'te.

### Tuzak 1 — takip edilen dosyada sessiz kalır

`check-ignore` varsayılan olarak **index'e de bakar**. Bir dosya zaten tracked ise,
pattern onu birebir yakalıyor olsa bile çıktı **boş** döner:

```bash
git add -f app.log
git check-ignore -v app.log             # cikti yok, exit=1
git check-ignore -v --no-index app.log  # .gitignore:1:*.log	app.log
```

Mantığı doğru: tracked dosya gerçekten ignore edilmiyor — `.gitignore` yalnızca
**untracked** dosyaları etkiler (notun başındaki kural). Ama teşhis sırasında yanıltır:
"pattern'ım yanlış" dersin, oysa pattern doğru, dosya sadece geçmişte `git add`
edilmiştir. <span style="color:#FFD600">**Çözüm `git rm --cached <path>`, pattern'ı değiştirmek değil.**</span> 

**Kural: "pattern doğru mu?" sorusunda `--no-index`, "bu dosya şu an ignore'lu mu?"
sorusunda bayraksız kullan.** İki farklı soru.

### Tuzak 2 — trailing slash

```bash
git check-ignore -v __pycache__      # eşleşme YOK
git check-ignore -v __pycache__/     # .gitignore:3:__pycache__/
git check-ignore -v src/__pycache__  # eşleşir (klasör diskte varsa)
```

Sebep: `__pycache__/` kalıbındaki sondaki `/` "sadece klasör" demek. Diskte o isimde bir
şey yoksa git verdiğin string'in klasör mü dosya mı olduğunu bilemez, o yüzden
klasör-kalıbıyla eşleştirmez. Sona `/` koyduğun an eşleşir.

`data/raw` eşleşir çünkü içinde `/` var — git `data`'nın klasör olduğunu string'den anlar.

**Pratik kural: klasör pattern'larını test ederken içindeki gerçek bir dosyayı sor.**
`.venv/` yerine `.venv/pyvenv.cfg`, `__pycache__/` yerine `src/x/__pycache__/a.pyc`.
Hem trailing-slash belirsizliğinden kaçarsın, hem gerçek hayattaki soruyu sorarsın —
`git status`'u kirletecek olan zaten o dosyadır.

### Tuzak 3 — negation (`!`) ve `-v` birlikte yanıltır

0.5'te yaşandı. `.gitignore`'da şu üçlü var:

```
.env
.env.*
!.env.example
```

`.env.example`'ın gerçekten commit'lenebildiğini doğrulamak için:

```bash
git check-ignore -v .env.example; echo $?
```
```
.gitignore:24:!.env.example	.env.example
0
```

**Çıktı da var, exit code da 0.** İkisi de "ignore'lu" der gibi görünüyor. Oysa dosya
`git status`'ta görünüyordu — yani ignore'lu **değil**.

#### Barış önce şöyle sandı

*"Çıktı geldiyse ve exit 0 ise dosya ignore'ludur."*

**Aslında `-v` bayrağı exit code'un anlamını değiştiriyor:**

| Komut | 0 ne demek |
|---|---|
| `git check-ignore <yol>` | Yol **ignore'lu** |
| `git check-ignore -v <yol>` | Yol bir pattern ile **eşleşti** — negation dahil |

`!` ile başlayan bir pattern de bir eşleşmedir; verbose mod onu "eşleşme bulundu" sayar.
Çıktıdaki `!` işareti zaten kararın kendisidir: *"eşleşti, ve karar ignore **etme**"*.

Doğrusu, bayraksız:

```bash
git check-ignore .env.example; echo $?   # cikti yok, exit=1  -> ignore'lu DEGIL
git check-ignore .venv/pyvenv.cfg; echo $?  # yolu basar, exit=0  -> ignore'lu
```

#### Genel ders

Bu, Tuzak 1'in aynı ailesinden: **`check-ignore` bir teşhis aracıdır, doğrulama aracı
değil.** Cevapladığı soru "bu yola karar veren pattern hangisi", "bu dosya commit'lenir
mi" değil.

Commit'lenip commit'lenmeyeceğini soruyorsan git'in gerçek davranışına bak:

```bash
git status                 # gorunuyor mu
git add -n .env.example    # dry-run: "add '.env.example'" derse ignore'lu degil
```

Bir aracın özet raporuna değil, aracın gerçekte ne yaptığına bakmak — bu notun en
başındaki inline-yorum dersinin aynısı. Orada da doğrulama **örnek** üzerinden yapılmıştı
ve pattern'ların yarısının bozuk olduğu 0.4'e kadar fark edilmemişti.

> **Kural:** `check-ignore` → "neden?" · `status` / `add --dry-run` → "gerçekten mi?"

### Tersten doğrulama: `check-ignore` yerine `status`

`check-ignore` "bu yolu ignore ediyor muyum?" sorusunu cevaplar — yani **ne soracağını
bilmen gerekir.** Aklına gelmeyen dosyayı test edemezsin. Tersten bakan iki komut:

```bash
git status --short --ignored   # ignore'lular "!!" ile listelenir
git status --short             # kirli olan ne varsa
```

`--ignored`, `.gitignore`'ın gerçekten neyi yuttuğunu gösterir. Bir kaynak dosyanın
oraya düştüğünü görürsen, pattern'ın fazla geniş demektir — notun başındaki
`raw` vs `raw/` tuzağının yakalandığı yer burasıdır.

**İkisi birlikte kullanılır:** `check-ignore` yazdığın satırı doğrular (ileriye doğru),
`status --ignored` yazmadığın satırın yan etkisini gösterir (geriye doğru).

## Bonus: `git status` "M" diyor ama `git diff` boş

Bunu yaşadık. Sebep: `git status` pasif bir okuma **değildir**.

Git her dosyanın boyutunu ve mtime'ını **index** dosyasında önbellekler (stat cache).
`status` çalışırken diskteki gerçek değerlerle karşılaştırır; farklıysa dosyanın içeriğini
okur ve index'i tazeler. Bu tazeleme bir **yazma** işlemidir ve `.git/index.lock` gerektirir.

Yazma izni yoksa (bizim durumda salt-okunur bir ortamdan çalıştırıldı) git index'i
tazeleyemez, elindeki bayat stat bilgisiyle "değişmiş olabilir" der:

```
warning: unable to unlink '.git/index.lock': Operation not permitted
 M .gitignore
```

**Kural: `git status` "M" der ama `git diff` boşsa, dosya değişmemiştir.**
İçerik karşılaştırması otoritedir, stat cache değil.

Aynı durum normal kullanımda da olur: dosyaya `touch` atarsan veya bir editör aynı içeriği
yeniden kaydederse mtime değişir, git bir an "modified" gösterir, `git status`'ü tekrar
çalıştırınca kendiliğinden düzelir (çünkü bu kez index'i tazeleyebilir).

Genel ders — bu projede tekrar tekrar karşımıza çıkacak: **cache ile gerçek arasında sapma
olabilir. Şüphede kaldığında cache'e değil kaynağa bak.** `PROGRESS.md` vs `git log`
ilişkisi de aynı problem.

# 01 — Git temelleri ve `.gitignore`

> Adım 0.1 · 2026-08-07

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

## Doğrulama komutu

```bash
git check-ignore -v <path> [<path> ...]
```

Hangi **satırın** hangi dosyayı ignore ettiğini gösterir. Sadece ignore edilen yollar
çıktıda görünür.

### Sürpriz davranış

```bash
git check-ignore -v __pycache__      # eşleşme YOK
git check-ignore -v __pycache__/     # .gitignore:1:__pycache__/
git check-ignore -v src/__pycache__  # eşleşir (klasör diskte varsa)
```

Sebep: `__pycache__/` kalıbındaki sondaki `/` "sadece klasör" demek. Diskte o isimde bir
şey yoksa git verdiğin string'in klasör mü dosya mı olduğunu bilemez, o yüzden
klasör-kalıbıyla eşleştirmez. Sona `/` koyduğun an eşleşir.

`data/raw` eşleşir çünkü içinde `/` var — git `data`'nın klasör olduğunu string'den anlar.

# 08 — Sanal ortamlar, paket kurulumu ve `uv`

> Adım 0.4 · 2026-08-10

Bu not üç soruyu cevaplıyor: sanal ortam **neyi** çözüyor, `pip install -e .`'deki `-e`
**ne yapıyor**, ve `uv` klasik `venv` + `pip` yolunun **neresine** giriyor.

Bilinmeyen terimler için en sonda [sözlük](#sözlük) var. Metin içinde ilk geçtikleri
yerde kısa parantezlerle de açıklandılar.

> **Kısa cevap** — Sanal ortam neyi çözer, `-e` ne yapar, `uv` bu resmin neresinde?
>
> 1. `site-packages` bir paketin tek sürümünü tutar; ikinci kurulum birinciyi sessizce ezer, çakışma bile vermez.
> 2. İzolasyon `activate`'te değil `pyvenv.cfg`'nin `include-system-site-packages = false` satırında; activate sadece `PATH` düzenler.
> 3. `pyproject.toml`'a `==` yazmak transitive bağımlılıkları serbest bırakır; abstract aralık toml'da, concrete kapanış lock'ta durur.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

---

## 1. Problem: tek bir ortak çöplük

Sanal ortam yokken `pip install` paketleri **tek bir ortak klasöre** yazar. Yerini
Python'ın kendisi söyler:

```bash
python -c "import sysconfig; print(sysconfig.get_path('purelib'))"
```

Çıktı `site-packages` diye biten bir yoldur. Kritik kural şu:

> **`site-packages` içinde bir paketin yalnızca tek bir sürümü bulunabilir.**

Çünkü paket orada `requests/` diye tek bir klasördür. İkinci bir kurulum birinciyi
**ezer**.

### Barış önce şöyle sandı

*"İki proje farklı sürüm isterse çakışma olur."*

**Aslında çakışma olmaz — sessiz kayıp olur.** Çakışma gürültülüdür, fark edersin.
Burada olan şu:

| An | Ne oldu |
|---|---|
| A projesi için `pip install requests==2.28` | `site-packages/requests/` → 2.28 |
| B projesi için `pip install requests==2.31` | Aynı klasör → 2.31. **2.28 gitti** |
| A projesini çalıştır | Patlar. A'nın kodunda tek satır değişmedi |

Buna **dependency hell** denir. Sanal ortamın çözdüğü problem tam olarak budur:
her projeye **kendi `site-packages`'ı**.

### İkinci sebep: sistem Python'ı işletim sisteminin aracıdır

Linux'ta `apt`, `firewalld`, `dnf` gibi araçlar sistem Python'ına bağlıdır. Oraya
yanlış bir `pip install` yaparsan işletim sistemi araçlarını bozarsın. Bu o kadar sık
yaşandı ki **PEP 668** ile standartlaştırıldı: modern Debian/Ubuntu artık sistem
Python'ına `pip install` yapmayı doğrudan reddeder —

```
error: externally-managed-environment
```

Bu bir görüş değil, kabul edilmiş bir Python standardı.

**Junior tuzağı:** `pip list` çıktısının uzunluğunu görüp sistem Python'ını
*temizlemeye* çalışmak. Doğru refleks oraya bir daha hiç dokunmamaktır.

---

## 2. `venv` nasıl çalışır — sihir yok, `PATH` var

### `python -m venv .venv` ne üretir

```
.venv/
├── pyvenv.cfg                    <- ortamin kimlik karti
├── Scripts/  (Windows)           <- python.exe, pip.exe, activate
│   veya bin/  (Linux/macOS)
└── Lib/site-packages/  (Windows) <- paketler buraya kurulur
    veya lib/pythonX.Y/site-packages/
```

`pyvenv.cfg` içeriği:

```ini
home = C:\Python313
include-system-site-packages = false
version = 3.13.1
```

| Satır | Ne yapar |
|---|---|
| `home` | Bu ortamın türetildiği **gerçek** Python kurulumu |
| `include-system-site-packages = false` | **İzolasyonun kendisi.** Sistem paketleri görünmez |
| `version` | Ortamın Python sürümü |

Python açılışta `site` modülünü çalıştırır; o da bu dosyayı okuyup `sys.prefix`'i
(Python'ın "kök klasörüm burası" değişkeni) `.venv`'e ayarlar. `site-packages` araması
oradan yapılır. Mekanizmanın tamamı bu — kopyalama, kayıt defteri, servis yok.

### `activate` tam olarak ne yapıyor

| İşlem | Sonuç |
|---|---|
| `.venv\Scripts` (veya `.venv/bin`) yolunu **`PATH`'in başına** ekler | `python` ve `pip` artık ilk orada bulunur |
| `VIRTUAL_ENV` ortam değişkenini set eder | Araçlar hangi ortamda olduklarını anlar |
| Prompt'a `(.venv)` yazar | Sadece görsel |
| Eski `PATH`'i saklar | `deactivate` geri koyar |

`PATH`, kabuğun bir komutu ararken **soldan sağa** taradığı klasör listesidir. `activate`
sadece bu listeyi düzenler. Başka hiçbir şey yapmaz.

### Kritik sonuç: `activate` zorunlu değil

```bash
.venv\Scripts\python.exe -c "import sys; print(sys.prefix)"
```

Bu, `activate` etmeden sanal ortamı kullanır. Çünkü ortamı belirleyen şey `PATH` değil,
**çalıştırdığın Python binary'sinin nerede olduğudur**. `activate` yalnızca yazma
kolaylığıdır.

**Prod'da ne kırılır:** CI (GitHub Actions) ve Docker'da interaktif kabuk yoktur;
`activate` çağrısı ya çalışmaz ya da bir sonraki adıma taşınmaz — çünkü her `RUN` /
her `step` yeni bir kabuktur, `PATH` değişikliği yaşamaz. Oralarda binary doğrudan
çağrılır (`/app/.venv/bin/python`) veya `ENV PATH=...` ile kalıcı yazılır. Bunu
bilmeyen junior, CI'da neden `ModuleNotFoundError` aldığını çözemez.

### Windows notları

| Kabuk | Komut |
|---|---|
| PowerShell | `.venv\Scripts\Activate.ps1` |
| cmd | `.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |

PowerShell'de execution policy hatası alırsan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### `.venv` neden `.gitignore`'lu

Yüzlerce MB ve **makineye özel**: `pyvenv.cfg` içinde mutlak yol var, `Scripts/*.exe`
platform-bağımlı. Başka makinede işe yaramaz. Kaynağı `pyproject.toml` + lock dosyası
olduğu için türetilebilir — not 01'in kuralı: *türetilebilen hiçbir şey git'e girmez.*

### Klasör adı neden `.venv`

Konvansiyon, resmî standart değil. `venv`, `env`, `.env` de görülür — ama `.env`
**kullanma**, sır dosyasıyla çakışır. `.venv` lehine pratik sebep: nokta ile başladığı
için listelerde öne çıkmaz, ve VS Code / PyCharm / `uv` bu ismi otomatik tanır.

---

## 3. Paketi kurmak: `pip install .` vs `pip install -e .`

### Neden paketi *kurmak* zorundayız

ADR-0002'de `src/` layout seçildi. Bunun bedeli: `src/` klasörü `sys.path`'te (Python'ın
modül ararken taradığı klasör listesi) **değildir**. Yani repo kökünde:

```bash
python -c "import lastfm_etl"   # ModuleNotFoundError
```

Paket kurulmadan import edilemez. 0.3'ün doğrulaması bu yüzden 0.4'e ertelendi —
kuracak bir ortam yoktu.

**Junior tuzağı:** import çalışmayınca koda `sys.path.append(...)` yazmak veya
`PYTHONPATH` ile idare etmek. İkisi de "bende çalışıyor"un ta kendisidir: proje yalnızca
o klasörden, o kabuktan çalışır. CI'da ilk patlayan şey budur.

### `pip install .` — kopyalar

```
src/lastfm_etl/__init__.py  ──kopya──>  .venv/Lib/site-packages/lastfm_etl/__init__.py
```

Kaynağı değiştirirsen kurulu kopya eski kalır. Her değişiklikte yeniden kurman gerekir.
Geliştirme sırasında kullanılamaz.

### `pip install -e .` — yönlendirir

`-e` = `--editable`. Kodu kopyalamaz; `site-packages`'a bir **yönlendirme** yazar
(`__editable__*.pth` dosyası veya bir import finder). `import lastfm_etl` dediğinde
Python doğrudan `src/lastfm_etl/`'i okur. Kaynağı düzenlersin, bir sonraki çalıştırmada
geçerlidir.

Bu bir gelenek değil, standarttır: **PEP 660** (*Editable installs for pyproject.toml
based builds*).

Sondaki `.` "kurulacak paketin kaynağı **bulunduğum klasör**" demek — pip oradaki
`pyproject.toml`'u okur.

| | `pip install .` | `pip install -e .` |
|---|---|---|
| Kod nereye gider | `site-packages`'a kopyalanır | Kopyalanmaz, yönlendirme yazılır |
| Kaynağı düzenleyince | Yeniden kurmak gerekir | Anında geçerli |
| Nerede kullanılır | Docker, prod, CI'da paket testi | Geliştirme |
| Yan ürün | `dist-info` | `dist-info` + `*.egg-info/` |

**Prod'da ne kırılır:** `-e` prod'a gitmez. Docker image'ında (8.7) `pip install .`
kullanılır, çünkü orada kaynak klasörünün image içinde kalmasını istemezsin —
yönlendirme kırık bir yola işaret eder. `-e` bir geliştirme aracıdır, deploy aracı değil.

### `*.egg-info/` ve `dist-info` nedir

Kurulum sırasında üretilen **paket metadata'sı**: paket adı, sürümü, bağımlılıkları,
hangi dosyaların pakete ait olduğu. Kaynağı `pyproject.toml` olduğu için türetilmiştir,
`.gitignore`'ludur. `egg-info` eski setuptools formatı, `dist-info` günümüz standardı
(**PEP 376**); editable kurulumda ikisi birden görülebilir.

### Arka planda ne oluyor: build backend, wheel, sdist

`pip install .` dediğinde pip paketi doğrudan kopyalamaz. Şu zinciri çalıştırır:

```
pyproject.toml  ──>  build backend  ──>  wheel  ──>  site-packages
   (tarif)          (setuptools)      (paket dosyasi)   (kurulum)
```

| Terim | Ne demek |
|---|---|
| **build backend** | Kaynağı kurulabilir pakete çeviren kütüphane. Bizde `setuptools` (`pyproject.toml`'un `[build-system]` bölümünde yazılı). Alternatifler: `hatchling`, `flit`, `pdm-backend`, `maturin` (Rust için) |
| **wheel** (`.whl`) | Önceden hazırlanmış, kurulumu sadece "aç ve kopyala" olan paket formatı (**PEP 427**). Hızlı |
| **sdist** (source distribution, `.tar.gz`) | Kaynak kodun kendisi. Kurulurken önce derlenip wheel'e çevrilmesi gerekir. Yavaş |
| **PEP 517 / 518** | pip ile build backend arasındaki sözleşmeyi tanımlayan standartlar. `pyproject.toml`'un `[build-system]` bölümü bu yüzden var |

Bunu bilmenin pratik faydası: bir kurulum çok uzun sürüyorsa, muhtemelen o paketin
platformun için hazır wheel'i yoktur ve kaynaktan derleniyordur.

---

## 4. Bağımlılık yönetimi: abstract vs concrete

### Barış önce şöyle sandı

*"Sürümü sabitlemek için `pyproject.toml`'a `dependencies = ["requests==2.31.0"]`
yazarım."*

Çalışır, ama iki sebeple yanlış.

### Sebep 1 — transitive bağımlılıkları kapsamaz

**Transitive (geçişli) bağımlılık:** senin doğrudan istemediğin, ama istediğin paketin
ihtiyaç duyduğu paket.

```
requests==2.31.0        <- senin pin'ledigin
├── urllib3             <- serbest
├── certifi             <- serbest
├── charset-normalizer  <- serbest
└── idna                <- serbest
```

`requests`'i sabitledin, altındaki dördü serbest. Ev makinende `urllib3 2.0.7`,
iş makinende üç ay sonra `2.5.0` kurulur. `pyproject.toml` iki makinede birebir aynı,
**ortamlar farklı**. "Bende çalışıyor" tam buradan doğar — ve pin yaptığın için
çözdüğünü sanırsın, asıl tehlikeli olan bu.

Gerçek bir projede doğrudan 5 bağımlılık, toplamda 60+ paket demektir. Elle takip
edilemez.

### Sebep 2 — `pyproject.toml` farklı bir soruyu cevaplar

| | Nerede yaşar | Neyi söyler | Örnek |
|---|---|---|---|
| **Abstract** (soyut) | `pyproject.toml` | "Bu paket **neyle uyumlu**" | `requests>=2.28` |
| **Concrete** (somut) | Lock dosyası | "**Tam olarak neyi** kurdum" | `requests==2.31.0` + `urllib3==2.0.7` + ... + hash'ler |

`pyproject.toml`'a `==` yazmak, uyumluluk beyanını kurulum kaydı yerine kullanmaktır.
Paketin bir gün başka bir projeye bağımlılık olarak girerse çözülemeyen çakışmalar
yaratır.

**İstisna:** uygulamalarda (bizim gibi) `pyproject.toml`'da geniş aralık + lock dosyası;
kütüphanelerde lock commit'lenmez, sadece aralık yayınlanır. Ayrım, paketi **başkasının
kurup kurmayacağıdır.**

### Sürüm aralığı operatörleri

| Yazım | Anlamı |
|---|---|
| `requests` | Herhangi bir sürüm. Riskli |
| `requests>=2.28` | 2.28 ve üstü |
| `requests>=2.28,<3` | 2.28 ve üstü, ama 3.0'a geçme |
| `requests~=2.28` | "Compatible release" — `>=2.28, <3.0` ile eşdeğer (**PEP 440**) |
| `requests==2.31.0` | Tam sabitleme (pin) |

Bunlar **semantic versioning** (`MAJOR.MINOR.PATCH`) varsayımına dayanır: MAJOR
değişince geriye dönük uyumluluk kırılır. Bir konvansiyondur, garanti değil — paket
yazarı uyabilir de uymayabilir de.

### Lock dosyası nedir

Bir kurulumun **tam kaydı**:

- Her paketin **tam** sürümü (transitive olanlar dahil)
- Her dosyanın **hash**'i (kriptografik parmak izi — indirilen dosyanın beklenen dosya
  olduğunu kanıtlar; supply-chain saldırılarına karşı koruma)
- Hangi paketin **neden** kurulduğu

Lock dosyası commit'lenir. Amacı **reproducible build**: aynı lock dosyasından, farklı
makinede, altı ay sonra **birebir aynı** ortam.

`pip freeze > requirements.txt` bunun ilkel hâlidir: hash yok, hangi paketin neden
kurulduğu belli değil, dev/prod ayrımı yok, platform farkı yönetilemiyor.

**PEP 751** standart bir lock formatı tanımlıyor (`pylock.toml`). `uv.lock` bu standart
değil, uv'ye özel — ama `uv export` ile `requirements.txt` veya `pylock.toml` üretilebilir.

---

## 5. `uv` nedir

Astral'ın (ruff'ı yapan ekip) Rust ile yazdığı, birden fazla aracın işini tek binary'de
toplayan paket yöneticisi.

| Klasik araç | Ne yapardı | `uv` karşılığı |
|---|---|---|
| `venv` | Sanal ortam oluştur | `uv venv` |
| `pip` | Paket kur | `uv pip install` / `uv add` |
| `pip-tools` | Lock üret | `uv lock` (otomatik) |
| `pipx` | CLI aracını izole kur | `uv tool install` |
| `pyenv` | Python sürümü yönet | `uv python install` |

**Önemli:** `uv` mekanizmayı gizlemiyor. `uv venv` yine `.venv/` üretir, yine
`pyvenv.cfg` yazar, yine `PATH` ile çalışır. Poetry'nin eski günlerindeki gibi kendi
dünyasını kurmuyor; komut isimleri bile pip'ten alınmış.

### İki kullanım modu

**pip-uyumlu mod** — pip'in yerine geçer, alışkanlıkların değişmez:

```bash
uv venv
uv pip install -e .
```

**project mode** — `pyproject.toml` + `uv.lock` üzerinden çalışır, ortamı senin yerine
yönetir:

```bash
uv add requests      # pyproject'e yazar + lock'u gunceller + kurar
uv sync              # lock'tan ortami birebir kurar
uv run python x.py   # ortam otomatik hazir, activate gerekmez
```

Bu projede **project mode** seçildi (ADR-0003).

### Komut sözlüğü

| Komut | Ne yapar | Klasik karşılığı |
|---|---|---|
| `uv venv` | `.venv/` oluşturur | `python -m venv .venv` |
| `uv venv --python 3.12` | Belirli sürümle ortam kurar (yoksa indirir) | `pyenv install` + `python -m venv` |
| `uv python install 3.12` | Python yorumlayıcısının kendisini indirir | `pyenv install 3.12` |
| `uv pip install -e .` | Projeyi editable kurar | `pip install -e .` |
| `uv add requests` | Bağımlılığı **`pyproject.toml`'a yazar**, lock'u günceller, kurar | `pip install` + elle toml düzenleme |
| `uv add --dev pytest` | Dev bağımlılığı olarak ekler (**PEP 735** `[dependency-groups]`) | Ayrı `requirements-dev.txt` |
| `uv remove requests` | Bağımlılığı kaldırır, lock'u günceller | `pip uninstall` + elle toml |
| `uv lock` | `uv.lock`'u yeniden çözer | `pip-compile` |
| `uv sync` | Ortamı **lock'a birebir eşitler** — fazlalıkları da siler | `pip install -r requirements.txt` (silme yok) |
| `uv sync --frozen` | Lock'u güncellemeden kurar. **CI'da kullanılır** | — |
| `uv run <komut>` | Ortamı hazırlayıp komutu çalıştırır | `activate` + komut |
| `uv tree` | Bağımlılık ağacını gösterir | `pipdeptree` |
| `uv export` | `requirements.txt` / `pylock.toml` üretir | — |

İki komutun farkı en çok karıştırılan yer:

- **`uv lock`** — "hangi sürümler kurulmalı" sorusunu çözer, dosyaya yazar. Ortama
  dokunmaz.
- **`uv sync`** — lock'u okur, ortamı ona **eşitler**. Lock'ta olmayan paketi ortamdan
  **siler**. Bu silme davranışı `pip install -r`'da yoktur ve tam olarak "ortamım
  temiz mi" garantisini veren şeydir.

---

## 6. Artılar, eksiler, riskler

### `uv` lehine

| Artı | Somut karşılığı |
|---|---|
| Lock dosyası dahili | ROADMAP 8.6 ("bağımlılık sabitleme") bedavaya gelir |
| Hız | CI süresi (8.5) ve Docker build (8.7) ciddi kısalır |
| Dev/prod ayrımı standart | `uv add --dev` — PEP 735 |
| Python sürümü yönetimi dahil | İki makinede farklı Python sürümü problemi çözülür |
| `uv sync` fazlalıkları siler | "Ortamımda ne var" sorusunun kesin cevabı |
| Tek araç | `venv` + `pip` + `pip-tools` + `pyenv` yerine bir binary |

### `uv` aleyhine — dürüst liste

| Eksi | Açıklama |
|---|---|
| Genç araç (2024) | API ve davranış hâlâ değişebiliyor; rehberler hızlı eskiyor |
| Ayrı kurulum gerekir | Python'la gelmiyor. Yeni gelen biri önce `uv`'yi kurmalı — README'de yazılmalı |
| `uv.lock` standart değil | uv'ye özel format. `uv export` ile çıkış var, ama üçüncü parti araçların (bazı güvenlik tarayıcıları) doğrudan okuyamaması mümkün |
| Tek şirkete bağlı | Astral ticari bir şirket. Açık kaynak (Apache-2.0/MIT) ama yön belirleyen tek aktör |
| Soyutlama riski | `uv run` her şeyi hallettiği için `PATH`/`pyvenv.cfg` mekanizmasını hiç öğrenmeden kullanmak mümkün — bu notun 2. bölümü tam bu riske karşı yazıldı |

### `venv` + `pip` lehine

Sıfır kurulum, sıfır risk, stdlib. Her makinede, her CI imajında zaten var. Bir aracın
"ne yaptığını" öğrenmek istiyorsan referans nokta budur.

### Neden yine de `uv` seçildi

"Önce ilkel yolu öğren, sonra `uv`'ye geç" fikri makul görünür ama burada **daha fazla**
araç öğrenmek demektir:

```
venv + pip  ->  pip-tools (8.6'da lock lazim)  ->  uv     = 3 arac
uv                                                        = 1 arac
```

Ve `uv` klasik mekanizmayı zaten gizlemiyor — aynı `.venv/`, aynı `pyvenv.cfg`, aynı
`PATH`. Yani "önce ilkel yol" ile öğrenilecek olan şey, `uv` ile de öğreniliyor.

Kilitlenme (lock-in) riski düşük: `uv` standart `pyproject.toml` kullanır. Bırakırsan
`uv.lock`'u silersin, `pyproject.toml` olduğu gibi kalır.

Gerekçenin tamamı ADR-0003'te.

---

## 7. Mülakat

**"Sanal ortam neden gerekli?"**
→ *"`site-packages` bir paketin tek sürümünü tutabilir; ikinci kurulum birincisini ezer.
Sanal ortam her projeye kendi `site-packages`'ını verir. Ayrıca sistem Python'ı
işletim sisteminin aracıdır — PEP 668 artık oraya kurulumu reddediyor."*

**"`pip install -e .`'deki `-e` ne yapar?"**
→ *"Editable install, PEP 660. Kodu `site-packages`'a kopyalamak yerine kaynağa
yönlendirme yazar; geliştirirken her değişiklikte yeniden kurmayı önler. `src/` layout
kullanıyorsan zaten paketi kurmadan import edemezsin. Prod'a `-e` gitmez."*

**"`pyproject.toml`'a sürüm pin'lemek yeterli mi?"**
→ *"Hayır. Transitive bağımlılıklar serbest kalır ve asıl sapma orada olur.
`pyproject.toml` abstract aralığı, lock dosyası concrete kapanışı tutar — ikisi farklı
soruları cevaplar."*

**"Neden `uv`?"**
→ *"Lock, dev/prod ayrımı ve Python sürüm yönetimini tek araçta veriyor, CI ve Docker
süresini kısaltıyor. Standart `pyproject.toml` kullandığı için bırakma maliyeti düşük.
Riski genç bir araç olması ve `uv.lock`'un henüz PEP 751 standardı olmaması."*

---

## Sözlük

| Terim | Anlamı |
|---|---|
| **binary** | Derlenmiş, doğrudan çalıştırılabilir program dosyası (`python.exe`, `uv.exe`) |
| **build backend** | Kaynak kodu kurulabilir pakete (wheel) çeviren kütüphane. Bizde `setuptools` |
| **dependency hell** | Farklı projelerin/paketlerin çelişen sürüm istekleri yüzünden ortamın çözülemez hâle gelmesi |
| **dist-info** | Kurulmuş paketin metadata klasörü (PEP 376). Ne kurulu, hangi sürüm, hangi dosyalar |
| **editable install** | Kaynağa yönlendiren kurulum (`-e`). PEP 660 |
| **entry point** | Paketin dışarıya açtığı komut veya eklenti kancası. `pyproject.toml`'da `[project.scripts]` |
| **hash** | Dosyanın kriptografik parmak izi. Lock dosyasında, indirilen dosyanın beklenen dosya olduğunu kanıtlar |
| **lock file** | Bir kurulumun tam kaydı: tüm paketler, tam sürümler, hash'ler |
| **PATH** | Kabuğun komut ararken soldan sağa taradığı klasör listesi (ortam değişkeni) |
| **PEP** | *Python Enhancement Proposal* — Python'ın resmî standart/öneri dokümanları. Numaralıdır |
| **pin** | Sürümü tam olarak sabitlemek (`==2.31.0`) |
| **reproducible build** | Aynı girdiden, farklı makinede, farklı zamanda birebir aynı çıktıyı üretebilme |
| **resolver** | Sürüm aralıklarından tutarlı bir kombinasyon hesaplayan algoritma. `uv`'nin hızlı olduğu yer |
| **sdist** | Source distribution — kaynak kod arşivi (`.tar.gz`). Kurulurken derlenmesi gerekir |
| **semantic versioning** | `MAJOR.MINOR.PATCH` konvansiyonu. MAJOR artışı geriye uyumluluğun kırıldığı anlamına gelir |
| **site-packages** | Kurulan paketlerin fiziksel olarak durduğu klasör |
| **stdlib** | Standart kütüphane — Python'la birlikte gelen, ayrıca kurulmayan modüller (`venv`, `pathlib`, `json`) |
| **supply-chain saldırısı** | Bağımlılık zincirine zararlı kod sokma. Hash doğrulaması buna karşı savunmadır |
| **sys.path** | Python'ın modül ararken taradığı klasör listesi |
| **sys.prefix** | Python'ın "kök klasörüm" değişkeni. Sanal ortamda `.venv`'i gösterir |
| **transitive dependency** | Doğrudan istemediğin, ama bağımlılığının ihtiyaç duyduğu paket |
| **wheel** | Önceden hazırlanmış paket formatı (`.whl`, PEP 427). Kurulumu hızlıdır |

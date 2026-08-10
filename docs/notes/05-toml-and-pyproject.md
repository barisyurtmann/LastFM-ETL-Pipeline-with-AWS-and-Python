# TOML ve `pyproject.toml`

## TOML nedir

**TOML** = *Tom's Obvious, Minimal Language*. Tom Preston-Werner (GitHub kurucularından)
tarafından 2013'te tasarlanmış bir **konfigürasyon dosyası formatı**. Programlama dili
değil, veri formatı — JSON ve YAML ile aynı kategoride.

Tasarım hedefi tek cümleyle: *insanın elle yazıp okuyabileceği, tek ve tartışmasız bir
şekilde parse edilebilen config formatı.*

Dosya uzantısı `.toml`, MIME tipi `application/toml`.

### Neden JSON değil

| Sorun | Açıklama |
|---|---|
| Yorum satırı yok | JSON spec'inde yorum yoktur. Config dosyasında "bu satır neden burada" yazamamak ağır bir kayıp |
| Sondaki virgül hatası | `{"a": 1,}` geçersizdir. Elle düzenlenen dosyalarda en sık yapılan hata |
| Çok satırlı string yok | Uzun bir açıklama veya komut yazmak `\n` kaçışlarıyla dolu tek satır demek |
| Her şey tırnak içinde | `{"name": "x", "version": "1.0"}` — göz yorucu |

JSON makineler arası veri değişimi için tasarlandı, insanın elle yazması için değil.
Config dosyası ise tam tersi bir kullanım.

### Neden YAML değil

YAML insan dostu ama ödediği bedel ağır:

| Sorun | Örnek |
|---|---|
| Girinti anlamlıdır | Yanlış hizalanmış bir boşluk sessizce farklı bir yapı üretir |
| Tip çıkarımı sürpriz yapar | Meşhur "Norway problem": `country: NO` → string değil, `False` |
| `yes`, `on`, `off` boolean olur | `password: no` diye yazarsan `False` alırsın |
| Spec devasa | YAML 1.2 spec'i ~80 sayfa; TOML ~10 sayfa. Farklı parser'lar farklı sonuç verebiliyor |

TOML tip çıkarımı yapmaz — bir şey string ise tırnak içindedir, nokta.

> Barış'ın notu: "config = YAML" refleksi yaygın ama Python paketleme dünyası bilinçli
> olarak TOML seçti. Bu bir moda değil, yukarıdaki sorunlara verilmiş bir cevap.

## TOML sözdizimi

Bilmen gereken her şey aşağıda. Format kasten küçük.

### Anahtar-değer

```toml
name = "lastfm-etl"
version = "0.1.0"
line_count = 42
ratio = 3.14
enabled = true
```

Değer tipleri: string, integer, float, boolean, tarih/saat, dizi, tablo.
**Tırnaksız string yoktur** — `name = lastfm` geçersizdir.

### Tablo (`[bolum]`)

```toml
[project]
name = "lastfm-etl"
version = "0.1.0"
```

Bir `[baslik]` satırından sonraki tüm anahtarlar o tabloya aittir — bir sonraki
tablo başlığına kadar. JSON karşılığı:

```json
{"project": {"name": "lastfm-etl", "version": "0.1.0"}}
```

### İç içe tablo (noktalı)

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Nokta iç içe geçmeyi ifade eder. JSON karşılığı:

```json
{"tool": {"setuptools": {"packages": {"find": {"where": ["src"]}}}}}
```

Ara seviyeleri (`[tool]`, `[tool.setuptools]`) ayrıca yazmak gerekmez, otomatik oluşur.

### Dizi

```toml
dependencies = ["requests>=2.31", "pydantic>=2.0"]

# cok satirli da yazilabilir, sondaki virgul serbesttir
dependencies = [
    "requests>=2.31",
    "pydantic>=2.0",
]
```

JSON'un aksine TOML sondaki virgüle izin verir. Diff'lerde tek satır değişmesi anlamına
gelir — küçük ama gerçek bir kazanç.

### Satır içi tablo

```toml
authors = [{ name = "Baris", email = "x@y.com" }]
```

Kısa yapılar için. Tek satırda kalmalıdır.

### Tablo dizisi (`[[...]]`)

```toml
[[tool.mypy.overrides]]
module = "pandas.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "boto3.*"
ignore_missing_imports = true
```

Çift köşeli parantez, aynı isimli tablodan **birden fazla** olduğunu söyler. JSON'da bir
liste içindeki nesnelere karşılık gelir.

### Yorum ve çok satırlı string

```toml
# Bu bir yorum

description = """
Birden fazla satira
yayilan metin
"""
```

## Python'da TOML okumak

```python
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
print(data["project"]["name"])
```

| Detay | Açıklama |
|---|---|
| `tomllib` | Python **3.11+** standart kütüphanesinde. Kurulum gerekmez |
| 3.11 öncesi | `tomli` paketi — `tomllib`'in aynısı, ayrı kurulur |
| Yazma desteği yok | `tomllib` sadece **okur**. Yazmak için `tomli-w` gerekir |
| Binary mod | Dosyadan okurken `open(path, "rb")` kullanılır — `tomllib.load()` binary dosya nesnesi bekler (encoding belirsizliğini önlemek için) |

Yazma desteğinin stdlib'de olmaması bilinçli: config dosyaları insan tarafından yazılır,
program tarafından değil. Program config dosyasını yeniden yazıyorsa yorumlar ve
biçimlendirme kaybolur.

---

# `pyproject.toml`

## Ne işe yarar

Bir Python projesinin **tek konfigürasyon dosyası**. İki ayrı iş yapar:

1. **Paketleme metadata'sı** — projenin adı, sürümü, bağımlılıkları, nasıl build
   edileceği
2. **Araç konfigürasyonu** — ruff, mypy, pytest, coverage gibi araçların ayarları

## Nasıl bu hâle geldi — kısa tarih

| Dönem | Dosya | Problem |
|---|---|---|
| ~2000–2016 | `setup.py` | **Çalıştırılabilir Python kodu.** Metadata'yı okumak için keyfi kod çalıştırmak gerekiyordu — güvenlik riski ve `pip` için tavuk-yumurta problemi |
| ~2016–2020 | `setup.cfg` | Deklaratif ama INI formatı: tip yok, her şey string, listeler satır sonlarıyla ayrılıyor |
| 2018+ | `pyproject.toml` | PEP 518 ile geldi, deklaratif, tipli, standart |

`setup.py`'nin asıl problemi şuydu: bir paketin bağımlılıklarını öğrenmek için o paketin
`setup.py`'sini **çalıştırmak** zorundaydın. O dosya `import numpy` diyorsa, numpy kurulu
değilse öğrenemiyordun. Ve keyfi kod çalıştırmak `pip install` sırasında güvenlik
yüzeyi demekti.

İlgili PEP'ler:

| PEP | Ne getirdi |
|---|---|
| **PEP 518** | `[build-system]` tablosu — build zamanı bağımlılıkları |
| **PEP 517** | Build backend arayüzü — setuptools tekelini kırdı |
| **PEP 621** | `[project]` tablosu — metadata'nın standart yeri |
| **PEP 508** | Bağımlılık ifade sözdizimi (`requests>=2.31; python_version < "3.11"`) |
| **PEP 639** | `license = "MIT"` — SPDX ifadeleriyle lisans |

## Üç ana bölüm

```toml
[build-system]     # Bu paket nasil build edilir
[project]          # Bu paket nedir
[tool.*]           # Araclarin ayarlari
```

### `[build-system]` — PEP 518

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"
```

| Anahtar | Anlamı |
|---|---|
| `requires` | Paketi **build etmek için** gereken araçlar. Çalışma zamanı bağımlılığı **değil** |
| `build-backend` | Wheel/sdist üretecek Python nesnesinin yolu |

Çözdüğü tavuk-yumurta problemi: `pip` bir paketi kurmak için önce build etmeli, build
etmek için bir araç gerekli, o aracın hangisi olduğunu öğrenmek için de dosyayı okumalı.
PEP 518 bu bilgiyi **statik** olarak dosyanın en başına koyar. `pip` bu listeyi okur,
**izole geçici bir ortama** kurar ve build'i orada yapar.

İzolasyon önemli: build araçların, senin projenin bağımlılıklarına karışmaz.

Backend seçenekleri:

| Backend | Karakteri |
|---|---|
| `setuptools.build_meta` | En yaygın, en çok karşına çıkar, en fazla ayar |
| `hatchling` | Modern, minimum config, src-layout'u sıfır ayarla bulur |
| `flit_core` | Çok basit saf-Python paketler için |
| `poetry.core` | Poetry kullanıyorsan |
| `maturin` | Rust uzantısı içeren paketler |

### `[project]` — PEP 621

Paketin kimliği. Tam alan listesi:

| Alan | Zorunlu | Ne işe yarar |
|---|---|---|
| `name` | evet | Dağıtım adı. `pip install <bu>` |
| `version` | evet* | Sürüm. `dynamic` ile başka yerden de alınabilir |
| `description` | hayır | Tek satırlık özet. PyPI'da başlığın altında görünür |
| `readme` | hayır | `"README.md"` — PyPI sayfasının gövdesi |
| `requires-python` | hayır | `">=3.11"`. pip yanlış sürüme kurmayı reddeder |
| `license` | hayır | PEP 639 ile SPDX: `license = "MIT"` |
| `authors` / `maintainers` | hayır | `[{ name = "...", email = "..." }]` |
| `keywords` | hayır | PyPI arama etiketleri |
| `classifiers` | hayır | PyPI'ın sabit kategori listesi (olgunluk, lisans, Python sürümü) |
| `dependencies` | hayır | **Çalışma zamanı** bağımlılıkları |
| `optional-dependencies` | hayır | İsteğe bağlı gruplar (`dev`, `test`, `aws`) |
| `urls` | hayır | Homepage, Repository, Issues linkleri |
| `scripts` | hayır | Komut satırı giriş noktaları |
| `gui-scripts` | hayır | Konsol penceresi açmayan sürümü |
| `entry-points` | hayır | Eklenti sistemleri için genel mekanizma |
| `dynamic` | hayır | "Bu alanı backend hesaplayacak" listesi |

### Bağımlılık sözdizimi — PEP 508

```toml
dependencies = [
    "requests>=2.31,<3",
    "pydantic-settings>=2.0",
    "pandas[parquet]>=2.0",
    "tomli>=2.0; python_version < '3.11'",
]
```

| Parça | Adı | Anlamı |
|---|---|---|
| `requests` | dağıtım adı | PyPI'daki isim |
| `>=2.31,<3` | version specifier | Sürüm aralığı. Virgül **VE** demektir |
| `[parquet]` | extra | O paketin isteğe bağlı bir özellik grubu |
| `; python_version < '3.11'` | environment marker | Koşullu bağımlılık — sadece koşul sağlanınca kurulur |

Sürüm operatörleri: `==`, `!=`, `>=`, `<=`, `>`, `<`, `~=` (compatible release),
`===` (birebir eşitlik).

`~=2.1` ifadesi `>=2.1, ==2.*` demektir — minor sürüm serbest, major kilitli.

### `optional-dependencies` — dev/prod ayrımı

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.6", "mypy>=1.11"]
aws = ["boto3>=1.34"]
```

Kurulum: `pip install -e ".[dev]"` veya `pip install -e ".[dev,aws]"`

Neden ayrı: `ruff` ve `pytest` üretimde çalışmaz. Lambda paketine girerlerse boşuna
boyut, boşuna güvenlik yüzeyi. Adım 9.5'te Lambda boyut limitine takılmamak için bu
ayrım gerçek bir işe yarayacak.

### `[project.scripts]` — komut üretmek

```toml
[project.scripts]
lastfm-etl = "lastfm_etl.main:app"
```

Bu satır, paket kurulduğunda `lastfm-etl` adında **çalıştırılabilir bir komut** üretir.
Format: `komut-adi = "modul.yolu:fonksiyon"`. Kurulum sırasında `bin/` (Windows'ta
`Scripts/`) altına küçük bir başlatıcı yazılır.

`python -m lastfm_etl.main` yazmak yerine `lastfm-etl` yazabilmek demek. Adım 6'da
CLI'ya geldiğimizde buraya döneceğiz.

### `[tool.*]` — araç konfigürasyonu

```toml
[tool.ruff]
line-length = 100

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`[tool]` altı **standartlaştırılmamıştır** — her araç kendi alt tablosunu tanımlar,
PyPI'daki isminden alır. Python paketleme otoriteleri bu alanın içine karışmaz.

Kazanç: eskiden `.flake8`, `setup.cfg`, `mypy.ini`, `pytest.ini`, `.coveragerc` diye
ayrı ayrı duran ayarlar tek dosyada toplanır. Adım 8'de bu bölüm belirgin şekilde
büyüyecek.

## Bu projede yazılan dosya

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "lastfm-etl"
version = "0.1.0"
description = "ETL pipeline for Last.fm listening history"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]
```

`[tool.setuptools.packages.find] where = ["src"]` satırı, setuptools'a paketleri
`src/` altında aramasını söyler. Bu olmadan setuptools repo kökünde arar ve
`docs`, `tests` gibi klasörleri paket sanmaya çalışır.

setuptools ≥61 `src/` düzenini otomatik algılayabiliyor, ama açık yazmak tercih edildi:
otomatik davranış sürüme göre değişebilir, açık konfigürasyon değişmez.

## Junior tuzağı

Sürümü iki yerde tutmak:

```toml
# pyproject.toml
version = "0.1.0"
```

```python
# src/lastfm_etl/__init__.py
__version__ = "0.1.0"   # <- ikinci kaynak, sapma garantili
```

Biri güncellenir, diğeri unutulur. Tek kaynak `pyproject.toml`'dur. Koda lazım olursa:

```python
from importlib.metadata import version
__version__ = version("lastfm-etl")   # dagitim adi girer, import adi degil
```

Dikkat: `version()` fonksiyonuna **dağıtım adı** (`lastfm-etl`) verilir, import adı
(`lastfm_etl`) değil. İkisinin farkı için bkz. not 06.

## Prod'da ne kırılır

`requires-python` yazılmazsa, paket Python 3.8'e de kurulur. Kod `match` ifadesi ya da
`tomllib` kullanıyorsa kurulum başarılı olur, **çalıştırma** anında patlar. Hata
kullanıcının makinesinde, kurulumdan günler sonra çıkar.

`dependencies` eksikse aynı sınıf hata: senin makinende `requests` başka bir paketin
bağımlılığı olarak zaten kuruludur, kod çalışır. Temiz bir makinede `ImportError`.
Bu, Docker'a geçince (Adım 8.7) hemen ortaya çıkar — Docker'ın en sevilen yan
faydalarından biri budur.

## Mülakat cevabı

> "`pyproject.toml` neden var, `setup.py` neyi yanlış yapıyordu?"

`setup.py` çalıştırılabilir koddu; metadata'yı okumak için keyfi kod çalıştırmak
gerekiyordu ve build araçlarının ne olduğunu önceden bilmenin yolu yoktu. PEP 518 build
gereksinimlerini statik hâle getirdi, PEP 517 build backend'i takas edilebilir yaptı,
PEP 621 metadata'yı standartlaştırdı. Yan fayda: araç konfigürasyonları da `[tool.*]`
altında tek dosyada toplandı.

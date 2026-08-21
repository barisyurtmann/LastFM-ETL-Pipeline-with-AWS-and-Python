#: ============================================================================
#: YORUMLU AYNA — src/lastfm_etl/config.py
#: ============================================================================
#: "#:" ile başlayan her satır açıklamadır ve gerçek dosyada YOKTUR.
#: Kalan her karakter src/lastfm_etl/config.py ile birebir aynıdır. Sapma kontrolü:
#:   grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/config.py | diff - src/lastfm_etl/config.py
#: Çıktı boşsa ayna güncel.
#:
#: Yazım sözleşmesi (2026-08-20'de değişti — eski "blok başına max 3 satır" kuralı kaldırıldı):
#:   NE    — bu sözdizimi/nesne aslında nedir, Python bununla ne yapar
#:   KANIT — iddiayı çalıştırarak doğrulayan komut
#:   BİZDE — bizim kodda tam olarak neyi değiştiriyor
#: Satır bütçesi yok. Bir kavram anlaşılana kadar yazılır. Bu dosya öğretir;
#: docs/notes/19 aynı konuların altı ay sonraki hatırlatma tablosudur.
#: Tasarım gerekçeleri (fail-fast, sır sızıntısı, araç seçimi): docs/notes/18
#:
#: ============================================================================
#: BÖLÜM 0 — ÖNCE ŞU ALTI KAVRAM
#: ============================================================================
#: Aşağıdaki kod bu altısını bilmeden okunmaz. Hiçbiri config.py'ye özel değil;
#: yazacağın her Python dosyasında aynı şekilde çalışırlar.
#:
#: ----------------------------------------------------------------------------
#: 0.1 — MODÜL, IMPORT VE "IMPORT ANI"
#: ----------------------------------------------------------------------------
#: NE: Bir .py dosyası bir "modül"dür. `import lastfm_etl.config` demek şudur:
#:     "bu dosyayı yukarıdan aşağı ÇALIŞTIR, sonra içinde oluşan isimleri bana ver."
#:     Import bir bildirim değil, bir çalıştırmadır.
#:
#:     Girintisiz (modül seviyesindeki) her satır o anda çalışır. `def` ve `class`
#:     satırları da çalışır — ama gövdeleri değil. `def f(): ...` satırının işi
#:     "f isminE bir fonksiyon nesnesi bağla"dır; gövde ancak f() çağrılınca çalışır.
#:
#:     Aynı modül ikinci kez import edilirse dosya TEKRAR ÇALIŞMAZ. Python ilk
#:     seferde sonucu sys.modules sözlüğüne koyar, sonraki importlar oradan gelir.
#:
#: KANIT:
#:   uv run python -c "import lastfm_etl.config as a, lastfm_etl.config as b; print(a is b)"
#:   # True  -> tek nesne, dosya bir kez çalıştı
#:   uv run python -c "import sys; import lastfm_etl.config; print('lastfm_etl.config' in sys.modules)"
#:
#: BİZDE: Satır 12 (logger = ...) ve satır 15 (REQUIRED_ENV_VARS = ...) modül
#:     seviyesindedir, yani import anında çalışır. Buna karşılık os.environ okuması
#:     BİLEREK modül seviyesine konmadı, load_config()'in içine kondu. Sebep:
#:     modül seviyesinde okunsaydı değer import anında donardı ve test ortam
#:     değişkenini değiştirse bile kod eski değeri görürdü. (docs/notes/18)
#:
#: ----------------------------------------------------------------------------
#: 0.2 — CLASS, INSTANCE VE self
#: ----------------------------------------------------------------------------
#: NE: `class` bir nesne KALIBIDIR; kendisi veri tutmaz. Kalıptan üretilen her
#:     nesneye "instance" (örnek) denir. Kalıp bir tanedir, instance bin tane olabilir.
#:
#:     Sınıfı ÇAĞIRMAK yeni bir instance üretir:
#:         c = Config(lastfm_api_key="abc")   # Config kalıp, c instance
#:
#:     Sınıf gövdesindeki `def`ler o instance'ın davranışıdır ve ilk parametreleri
#:     `self`tir. `self` = "üzerinde çalıştığın instance". Onu sen VERMEZSİN:
#:         c.__repr__()      Python bunu şuna çevirir:      Config.__repr__(c)
#:     İkisi aynı çağrıdır; noktalı yazım sadece kısayoldur.
#:
#:     `self` dilin ayrılmış kelimesi değil, sadece gelenektir. `def __repr__(kendisi)`
#:     de çalışır — ama yazma, her Python okuyucusu `self` bekler.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.config import Config, load_config
#:   c = load_config()
#:   print(c.__repr__() == Config.__repr__(c))   # True
#:   print(type(c) is Config, isinstance(c, Config))
#:   "
#:
#: BİZDE: Satır 39'daki self.lastfm_api_key "BU instance'ın alanı" demektir,
#:     sınıfın değil. İki farklı Config üretilseydi ikisinin key'i farklı olurdu.
#:
#: ----------------------------------------------------------------------------
#: 0.3 — DUNDER METOTLAR (__isim__)
#: ----------------------------------------------------------------------------
#: NE: İki alt çizgiyle sarılmış isimler ("dunder" = double underscore) dilin
#:     SÖZDİZİMİ ile senin nesnen arasındaki kancalardır. Kural: bunları sen
#:     çağırmazsın, Python çağırır. Sen sadece tanımlarsın.
#:
#:     | Sen bunu yazarsın | Python bunu çağırır                        |
#:     |-------------------|--------------------------------------------|
#:     | Config(x)         | __init__                                   |
#:     | repr(c)           | __repr__                                   |
#:     | str(c), print(c)  | __str__ — tanımlı DEĞİLSE __repr__'a düşer |
#:     | c == d            | __eq__                                     |
#:     | c.x = 1           | __setattr__                                |
#:     | len(c)            | __len__                                    |
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.config import load_config
#:   c = load_config()
#:   print(hasattr(type(c), '__str__'), str(c))   # __str__ yok, çıktı maskeli repr
#:   "
#:
#: BİZDE: İki dunder yazdık — __post_init__ (satır 31) ve __repr__ (satır 37).
#:     Kritik zincir: satır 62'de `logger.debug("...: %s", config)` yazıyor.
#:     Hiçbir yerde __repr__ çağrısı yok. Ama %s -> str(config) -> __str__ yok ->
#:     __repr__ -> maskeli metin. Sırrın loga sızmamasının sebebi bu zincirdir.
#:     Yani maskeleme, "her yerde dikkatli olmak"la değil, TİPİN kendisiyle sağlanıyor.
#:
#: ----------------------------------------------------------------------------
#: 0.4 — KALITIM (INHERITANCE)
#: ----------------------------------------------------------------------------
#: NE: `class ConfigError(RuntimeError):` = "ConfigError, RuntimeError'ın bir
#:     çeşididir". Parantez içindeki taban sınıftır. Alt sınıf tabanın her şeyine
#:     otomatik sahiptir; sen yalnızca FARKI yazarsın. Burada fark yok — istediğimiz
#:     tek şey yeni bir İSİM, çünkü isim yakalanabilir bir kimliktir.
#:
#:     Sonuç: `except RuntimeError` yazan kod bizim hatamızı da yakalar (genel ağ),
#:     `except ConfigError` yazan yalnızca bizimkini (dar ağ). İkisini birden istiyorduk.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.config import ConfigError
#:   print(issubclass(ConfigError, RuntimeError), issubclass(ConfigError, Exception))
#:   print([c.__name__ for c in ConfigError.__mro__])
#:   "
#:   # ConfigError -> RuntimeError -> Exception -> BaseException -> object
#:   # __mro__ = 'method resolution order': Python bir ismi ararken bu sırayla bakar.
#:
#: JUNIOR TUZAĞI: `raise Exception("config yok")` yazmak. Çağıran tarafı
#:     `except Exception` yazmaya, yani HER şeyi yakalamaya mahkûm eder — böylece
#:     senin config hatanla bir yazım hatası (TypeError) aynı kutuya düşer.
#:
#: ----------------------------------------------------------------------------
#: 0.5 — EXCEPTION VE raise
#: ----------------------------------------------------------------------------
#: NE: Exception bir NESNEDİR. Sınıfı hatanın türünü, argümanı mesajını taşır.
#:     `raise ConfigError("mesaj")` şunu yapar: bu satırda dur, fonksiyondan çık,
#:     çağırana dön. O da yakalamazsa onun çağıranına... Kimse yakalamazsa süreç ölür:
#:     traceback basılır ve çıkış kodu 1 olur.
#:
#:     Yakalama `try: ... except ConfigError as e: ...` ile yapılır. Bu dosyada hiç
#:     `try` yok — bilerek. Config eksikken devam etmenin anlamı yok (fail-fast).
#:
#:     raise ile return farkı: `return` bir DEĞER döndürür, akış normal devam eder.
#:     `raise` akışı İPTAL eder. Bir fonksiyonun "başaramadım" demesinin doğru yolu
#:     None döndürmek değil, raise etmektir; None döndürürsen çağıran kontrol etmeyi
#:     unutur ve hata üç kat aşağıda, alakasız bir satırda AttributeError olarak patlar.
#:
#: KANIT (Git Bash):
#:   LASTFM_API_KEY= uv run python -c "from lastfm_etl.config import load_config; load_config()"
#:   echo $?     # 1  -> yakalanmayan exception sürecin çıkış kodunu 1 yapar
#:   # Çıkış kodu önemli: cron/Airflow/Lambda "başarısız" olduğunu böyle anlar.
#:
#: ----------------------------------------------------------------------------
#: 0.6 — DOCSTRING
#: ----------------------------------------------------------------------------
#: NE: Bir modülün / sınıfın / fonksiyonun İLK ifadesi bir string literal ise o
#:     docstring'dir ve nesnenin __doc__ özniteliğinde ÇALIŞMA ZAMANINDA yaşar.
#:     Yorum (#) değildir: yorumlar derleme sırasında atılır, docstring atılmaz.
#:     help() bunu okur, editörün tooltip'i bunu gösterir.
#:
#:     Yan etki: gövdesi yalnızca docstring olan bir sınıf/fonksiyon GEÇERLİDİR;
#:     `pass` gerekmez, çünkü gövde boş değil. Satır 18-19 tam olarak budur.
#:
#: KANIT:
#:   uv run python -c "
#:   import lastfm_etl.config as m
#:   print(m.__doc__); print(m.load_config.__doc__); print(m.ConfigError.__doc__)
#:   "
#:
#: KONVANSİYON (PEP 257): ilk satır emir kipinde tek cümle, nokta ile biter.
#:     'Read, validate and cache configuration...' -> doğru.
#:     'This function reads the config' -> yaygın ama PEP 257 emir kipi ister.
#:
#: ============================================================================
#: BÖLÜM 1 — DOSYANIN KENDİSİ
#: ============================================================================
#: Aşağıdaki ilk satır modül docstring'i (bkz. 0.6): dosyanın en üstünde,
#: importlardan bile önce. Tek cümle, ne olduğunu söylüyor, nasıl olduğunu değil.
"""Application configuration, loaded once from the environment."""

#: PEP 8 import sırası: (1) standart kütüphane, (2) üçüncü parti, (3) yerel —
#: gruplar arasında bir boş satır. ruff bunu I001 kuralıyla zorlar.
#: dotenv ayrı grupta çünkü dışarıdan gelen tek bağımlılık; bir bakışta görülmeli.
#:
#: İki import biçiminin farkı:
#:   import logging               -> 'logging' adına MODÜL nesnesini bağlar. logging.getLogger(...)
#:   from dataclasses import ...  -> modülün içindeki ADLARI doğrudan bağlar. dataclass(...)
#: İkincisi daha kısa ama ismin nereden geldiğini gizler; stdlib'de yaygın olanı
#: karışık kullanmaktır: kısa/tanınmış adlar 'from', jenerik adlar 'import module'.
import logging
import os
from dataclasses import dataclass, fields
from functools import lru_cache
from typing import Final

from dotenv import find_dotenv, load_dotenv

#: ----------------------------------------------------------------------------
#: LOGGING — üç parça: Logger, Handler, Level
#: ----------------------------------------------------------------------------
#: NE:
#:   Logger  : mesajı ÜRETEN, isimli nesne. Kayıt defterinden alınır.
#:   Handler : mesajı bir YERE YAZAN nesne (konsol, dosya, CloudWatch). Ayrı takılır.
#:   Level   : eşik. DEBUG(10) < INFO(20) < WARNING(30) < ERROR(40) < CRITICAL(50)
#:
#:   logging.getLogger("a.b") bir OLUŞTURMA değil, bir ARAMA'dır: aynı isimle kaç
#:   kez çağırırsan çağır aynı nesneyi alırsın. Yani modülün her yerinden, her
#:   import'tan sonra tek bir logger vardır.
#:
#:   İsimler NOKTAYLA hiyerarşi kurar. Bizimki 'lastfm_etl.config'; ebeveyni
#:   'lastfm_etl', onun ebeveyni kök (root) logger'dır. Mesaj yukarı doğru akar ve
#:   HANDLER'I OLAN atalardan yayınlanır.
#:
#:   Bizim logger'ın handler'ı yok ve seviyesi ayarlı değil -> tek başına SESSİZDİR.
#:   Uygulama logging.basicConfig(...) çağırıp root'a handler takarsa mesaj görünür.
#:   Bu yüzden kütüphane/modül kodu ASLA basicConfig çağırmaz: çağırsaydı, bu modülü
#:   import eden herkesin log formatını gasp ederdi. setup_logging() P2.1'de gelecek.
#:
#: __name__ NEDİR: her modülde otomatik var olan bir değişken. Modül import
#:   edildiğinde değeri modülün tam adıdır ("lastfm_etl.config"); dosya doğrudan
#:   `python config.py` ile çalıştırılırsa "__main__" olur. getLogger(__name__)
#:   yazmanın anlamı: "logger'ın adı, bulunduğu modülün yolu olsun" — böylece log
#:   satırına bakınca mesajın hangi dosyadan çıktığı bellidir ve filtrelenebilir.
#:
#: KANIT:
#:   # a) kurulumsuz -> hiçbir çıktı yok
#:   uv run python -c "from lastfm_etl.config import load_config; load_config()"
#:   # b) root'a handler takılınca -> iki DEBUG satırı (config maskeli)
#:   uv run python -c "
#:   import logging; logging.basicConfig(level=logging.DEBUG)
#:   from lastfm_etl.config import load_config; load_config()
#:   "
#:   # c) logger'ın kimliği ve boşluğu
#:   uv run python -c "
#:   import lastfm_etl.config as m
#:   print(m.logger.name, m.logger.handlers, m.logger.level)   # ... [] 0
#:   "
# Module-level logger: no setup, no side effect. The application configures handlers.
logger = logging.getLogger(__name__)

#: ----------------------------------------------------------------------------
#: TYPE HINT, KÖŞELİ PARANTEZ VE TYPE CHECKER
#: ----------------------------------------------------------------------------
#: NE (annotation): `x: str` Python'a HİÇBİR ŞEY yaptırmaz. Kontrol yok, dönüşüm
#:   yok. Annotation sadece bir sözlüğe (__annotations__) yazılır. Yalan yazabilirsin:
#:       uv run python -c "x: int = 'abc'; print(x)"   # abc — hata yok
#:   Type hint bir ÇALIŞMA ZAMANI doğrulaması değil, bir SÖZLEŞMEDİR.
#:
#: NE (köşeli parantez): Final[...], tuple[str, ...], list[int] — bunlar tipi
#:   PARAMETRELEMEKtir. Kap tipi dışarıda, içindekinin tipi köşeli parantezte.
#:       tuple[str, ...]  = elemanları str olan, uzunluğu serbest tuple
#:       tuple[str]       = TAM 1 elemanlı tuple (farkı bu; kolay karıştırılır)
#:   Buradaki `...` gerçek bir nesnedir (Ellipsis) ve burada "uzunluk serbest" demektir.
#:
#: NE (type checker / mypy): Kodu ÇALIŞTIRMADAN okuyup annotation'ların birbiriyle
#:   tutarlı olup olmadığını söyleyen AYRI bir programdır. Python'un parçası değildir,
#:   ayrı kurulur (uv add --dev mypy) ve CI'da çalışır. Şu an projede KURULU DEĞİL —
#:   yani bugün bu satırlar yalnızca insana ve editöre bilgi veriyor.
#:
#: Final NE YAPAR: "bu isme bir daha atama yapılmayacak" der. Çalışma zamanında
#:   hiçbir şeyi kilitlemez; mypy yoksa uyarı da yoktur. Peki neden yazıyoruz?
#:   Çünkü annotation geçmişe dönük çalışır: mypy kurulduğu gün bu sözleşmeler
#:   denetlenmeye başlar. Sonradan tip eklemek, baştan yazmaktan kat kat pahalıdır.
#:
#: JUNIOR TUZAĞI: type hint'i doğrulama sanmak. Pydantic gerçekten doğrular
#:   (çalışma zamanında tip dönüştürür/hata verir); typing modülü DOĞRULAMAZ.
#:   İkisi aynı sözdizimini kullandığı için sürekli karıştırılır.
#:
#: BÜYÜK HARF: REQUIRED_ENV_VARS adının büyük harf olması "bu bir sabittir"
#:   konvansiyonudur (PEP 8). Dil bunu zorlamaz; Python'da gerçek sabit yoktur.
#:
#: NEDEN list DEĞİL tuple: tuple değiştirilemez. Biri yanlışlıkla .append() ederse
#:   liste sessizce büyür, tuple AttributeError verir. Sabit, değiştirilemez olmalı.
#: DİKKAT: tuple'ı VİRGÜL yapar, parantez değil. ("X") bir string'tir, ("X",) tuple.
#:   KANIT: uv run python -c "print(len(('X',)), len(('X')))"   # 1 14
# Every name here must be present and non-empty before the pipeline may start
REQUIRED_ENV_VARS: Final[tuple[str, ...]] = ("LASTFM_API_KEY",)


#: Kalıtım: bkz. 0.4 — bu sınıfın tek kazancı YAKALANABİLİR BİR İSİM olması.
#: Gövde yalnızca docstring: bkz. 0.6 — bu yüzden `pass` yazmaya gerek yok.
#:
#: NEDEN RuntimeError, ValueError değil: ValueError "bana verdiğin ARGÜMAN yanlış"
#:   der. Burada argüman yok; sorun sürecin içinde bulunduğu ORTAMDA. RuntimeError
#:   "çalışma anındaki koşullar uygun değil" demektir ve durum tam olarak budur.
#:   Bu bir stil tercihi değil, stdlib'in kendi ayrımıdır (bkz. Python docs, built-in
#:   exceptions) — ama hangi tabanın seçileceği projeden projeye tartışılır.
class ConfigError(RuntimeError):
    """Raised when required configuration is missing, empty or invalid."""


#: ----------------------------------------------------------------------------
#: @dataclass — SENİN YERİNE KOD YAZAN DEKORATÖR
#: ----------------------------------------------------------------------------
#: NE: dataclass, sınıfın __annotations__ sözlüğüne bakar, orada gördüğü her ad
#:   için sana metot YAZAR ve sınıfa ekler. Yani şunu yazmak:
#:
#:       @dataclass
#:       class Config:
#:           lastfm_api_key: str
#:
#:   kabaca şunu elle yazmaya denktir:
#:
#:       class Config:
#:           def __init__(self, lastfm_api_key: str) -> None:
#:               self.lastfm_api_key = lastfm_api_key
#:           def __repr__(self):
#:               return f"Config(lastfm_api_key={self.lastfm_api_key!r})"
#:           def __eq__(self, other):
#:               if other.__class__ is not self.__class__: return NotImplemented
#:               return (self.lastfm_api_key,) == (other.lastfm_api_key,)
#:
#:   Kazanç sadece tuş tasarrufu değil: 10 alanlı bir sınıfta elle yazılan __init__
#:   ve __eq__ er ya da geç bir alanı unutur. Üretilen kod unutmaz.
#:
#: KANIT (üretilmiş __init__ gerçekten var mı):
#:   uv run python -c "
#:   import inspect; from lastfm_etl.config import Config
#:   print(inspect.signature(Config))          # (lastfm_api_key: str) -> None
#:   print(Config.__annotations__)             # {'lastfm_api_key': <class 'str'>}
#:   "
#:
#: ÜÇ PARAMETRE — her biri ne yapıyor:
#:
#: frozen=True
#:   __setattr__ ve __delattr__ metotlarını ezer; atama denemesi FrozenInstanceError
#:   fırlatır. Yan kazanç: eq=True ile birlikte nesne hashable olur (set'e/dict
#:   anahtarına konabilir). DİKKAT: frozen DERİN DEĞİLDİR — alan bir liste olsaydı
#:   listenin İÇİ yine değiştirilebilirdi. Bizde str var, str zaten değişmez.
#:
#: slots=True
#:   Normalde her nesnenin öznitelikleri bir __dict__ sözlüğünde durur; bu yüzden
#:   `c.yeni_alan = 5` sessizce ÇALIŞIR. slots ile Python alanlara sabit yer ayırır,
#:   __dict__ HİÇ OLUŞMAZ -> tanımsız bir ada atama hata verir. Yazım hatası artık
#:   sessizce yeni bir alan yaratamaz. Ayrıca bellek kazancı sağlar.
#:   İNCE DETAY: slots=True olan bir dataclass'ta Python sınıfı yerinde değiştiremez,
#:   YENİ bir sınıf üretir. Bunun garip bir yan etkisi aşağıdaki ölçümde görünüyor.
#:
#: repr=False
#:   "dataclass __repr__ ÜRETMESİN" demektir. Üretseydi bütün alanları basardı,
#:   yani API anahtarını log'a ve traceback'e dökerdi (satır 37 bunu engelliyor).
#:   ÖLÇÜLEN GERÇEK: elle yazılmış bir __repr__ varsa dataclass zaten onun üstüne
#:   YAZMAZ — yani repr=False olmasa da maskeleme çalışırdı. Peki neden duruyor?
#:   Çünkü HATA MODUNU güvenli yapıyor: yarın biri satır 37'yi silerse,
#:     repr=False ile  -> <lastfm_etl.config.Config object at 0x...>   (sızıntı yok)
#:     repr=True ile   -> Config(lastfm_api_key='gerçek_anahtar')      (SIZINTI)
#:   Güvenlik kararları "kod doğruyken ne olur"a değil, "biri bir şeyi silerse ne
#:   olur"a göre verilir.
#:
#: DÜZELTME — docs/notes/19 KONTROL C YANLIŞ ÖLÇÜM VERİYOR:
#:   Not 19, olmayan bir alana atamanın AttributeError vereceğini söylüyor.
#:   Ölçüldü (hem 3.11 hem 3.14): frozen + slots BİRLİKTE kullanıldığında
#:     c.lastfm_api_key = "x"  -> FrozenInstanceError   (beklenen)
#:     c.lastfm_api_ky  = "x"  -> TypeError: super(type, obj)...   (AttributeError DEĞİL)
#:   Sebep: frozen'ın ürettiği __setattr__ kapanışta ESKİ (slots'suz) sınıfı tutar;
#:   slots yeni bir sınıf ürettiği için `type(self) is cls` yanlış çıkar ve kod
#:   super() dalına düşer. Yalnız slots (frozen'sız) kullanılsaydı AttributeError olurdu.
#:   İDDİA DOĞRU (typo sessizce geçmiyor), ÖLÇÜM YANLIŞTI. Not 19 düzeltilecek.
@dataclass(frozen=True, slots=True, repr=False)
class Config:
    """Validated runtime configuration.

    Frozen because configuration is a reading taken at startup, not a variable.
    """

    #: Bu satır SADECE bir annotation — değer yok. dataclass için anlamı:
    #:   lastfm_api_key: str          -> zorunlu alan, __init__ parametresi olur
    #:   lastfm_api_key: str = "abc"  -> varsayılanı olan alan (bunu istemiyoruz;
    #:                                   config'in sessiz varsayılanı olmamalı)
    #:   lastfm_api_key = "abc"       -> annotation YOK -> dataclass bunu ALAN SAYMAZ,
    #:                                   sıradan bir sınıf özniteliği olur. Sessiz tuzak.
    lastfm_api_key: str

    #: __post_init__ (bkz. 0.3): dataclass'ın ürettiği __init__, alanları atadıktan
    #: SONRA bu metodu kendisi çağırır. Sen çağırmazsın.
    #: Neden burada doğrulama: burada hata fırlatmak, GEÇERSİZ BİR Config NESNESİNİN
    #: HİÇ DOĞMAMASI demektir. load_config() seni yanlış ORTAMDAN korur; burası
    #: kodun kendisinden korur — testler ve gelecekte yazılacak her çağrı dahil.
    #: Buna "invariant" denir: tipin her örneği için her zaman doğru olan kural.
    def __post_init__(self) -> None:
        # Backstop invariant: no code path, not even a test, may build an invalid Config
        #: Bu tek satırda dört şey var:
        #:
        #: fields(self)  — dataclass'ın alan TANIMLARINI döndürür (Field nesneleri),
        #:                 değerlerini değil. Her Field'ın .name, .type, .default'u var.
        #:                 KANIT: uv run python -c "
        #:                 from dataclasses import fields; from lastfm_etl.config import Config
        #:                 print([(f.name, f.type) for f in fields(Config)])"
        #:
        #: getattr(self, f.name)  — `self.lastfm_api_key` ile AYNI şey. Fark: nokta
        #:                 yazımında öznitelik adını KOD YAZARKEN bilmen gerekir.
        #:                 getattr'da ad bir STRING'dir, yani çalışma zamanında hesaplanır.
        #:                 f.name burada "lastfm_api_key" string'i; nokta ile yazamayız.
        #:                 KANIT: uv run python -c "
        #:                 from lastfm_etl.config import load_config
        #:                 c = load_config(); print(getattr(c, 'lastfm_api_key') == c.lastfm_api_key)"
        #:
        #: .strip()      — string'in BAŞINDAKİ ve SONUNDAKİ boşluk karakterlerini
        #:                 (boşluk, tab, \n, \r) atıp YENİ bir string döndürür.
        #:                 Orijinali değiştirmez (string değişmezdir). Argümansız hali
        #:                 boşlukları atar; .strip("/") gibi karakter de verilebilir.
        #:                 KANIT: uv run python -c "print(repr('  a b \n'.strip()))"  # 'a b'
        #:                 Buradaki işi: "   " (üç boşluk) bir değer DEĞİLDİR; strip'ten
        #:                 sonra "" kalır ve `not ""` True olur.
        #:
        #: [... for ... if ...] — list comprehension; koşulu geçen alan ADLARINI toplar.
        #:                 Tek alan için fazla iş gibi duruyor ama ikinci alan
        #:                 eklendiğinde kontrol KENDİLİĞİNDEN onu da kapsar.
        #:
        #: PROD'DA NE KIRILIR: .strip() karşısındakinin str olduğunu VARSAYAR.
        #: İlk int/bool alan (örn. HTTP_TIMEOUT: int) eklendiği gün bu satır
        #: AttributeError verir. Çözüm o gün: isinstance(v, str) süzgeci ya da
        #: pydantic-settings'e geçiş (docs/notes/18 §6).
        blank = [f.name for f in fields(self) if not getattr(self, f.name).strip()]
        if blank:
            #: ", ".join(liste) — listedeki string'leri aralarına ", " koyarak TEK
            #: string'e birleştirir. Yönü ters gelir ama mantığı şu: ayırıcı kendisi
            #: birleştirmeyi yapar. join yalnızca string kabul eder; sayı listesinde
            #: TypeError verir (o zaman ", ".join(map(str, xs)) yazılır).
            #: KANIT: uv run python -c "print(', '.join(['a','b','c']))"   # a, b, c
            #: Neden döngüyle değil: join tek geçişte çalışır, elle += yapılan birleştirme
            #: her adımda yeni string yaratır — uzun listelerde ölçülebilir şekilde yavaştır.
            raise ConfigError(f"Config fields must not be empty: {', '.join(blank)}")

    #: __repr__ (bkz. 0.3): repr(c), print(c) ve "%s" bu metoda düşer. Amaç:
    #: nesnenin metin hâli HİÇBİR KOŞULDA gerçek anahtarı içermesin.
    #: [-4:] dilimlemesi taşmaz: 4 karakterden kısa string'te hata vermez, olanı döndürür
    #: ("ab" -> "***ab"). Yani kısa/bozuk bir key bile bu satırı patlatmaz.
    def __repr__(self) -> str:
        # The generated dataclass repr prints every field; this one must never leak the key
        return f"Config(lastfm_api_key='***{self.lastfm_api_key[-4:]}')"


#: ----------------------------------------------------------------------------
#: @lru_cache — FONKSİYONUN ETRAFINA SARILAN NESNE
#: ----------------------------------------------------------------------------
#: NE: Dekoratör, altındaki fonksiyonu alır ve onun yerine BAŞKA bir nesne koyar.
#:       @lru_cache(maxsize=1)
#:       def load_config() -> Config: ...
#:   harfi harfine şuna eşittir:
#:       def load_config() -> Config: ...
#:       load_config = lru_cache(maxsize=1)(load_config)
#:   Yani `load_config` artık senin yazdığın fonksiyon DEĞİL; içinde bir sözlük
#:   tutan _lru_cache_wrapper nesnesidir. Çağırınca önce sözlüğe bakar; argümanlar
#:   daha önce görülmüşse gövdeye HİÇ girmez, saklanan sonucu döndürür.
#:   ("LRU" = least recently used: sözlük dolunca en eski kullanılan atılır.)
#:
#: Argümansız fonksiyon + maxsize=1 -> gövde SÜREÇ BOYUNCA bir kez çalışır,
#:   her çağrı AYNI Config nesnesini döndürür. .env bir kez okunur, log bir kez düşer.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.config import load_config as l
#:   print(l() is l())            # True — aynı nesne
#:   print(l.cache_info())        # CacheInfo(hits=..., misses=1, maxsize=1, currsize=1)
#:   print(type(l).__name__)      # _lru_cache_wrapper — fonksiyon değil, sarmalayıcı
#:   print(l.__wrapped__)         # sarmalanan gerçek fonksiyon hâlâ burada
#:   "
#:
#: PROD'DA/TESTTE NE KIRILIR: test ortam değişkenini değiştirir (monkeypatch.setenv)
#:   ve load_config()'i tekrar çağırırsa ESKİ değeri alır — gövde çalışmaz. Bu yüzden
#:   testte load_config.cache_clear() ŞART. cache_clear metodu senin fonksiyonunda
#:   yok, sarmalayıcı nesnede var; lru_cache yazmasan öyle bir metot da olmazdı.
#:
#: ALTERNATİF ve NEDEN O DEĞİL: modül seviyesinde `config = load_config()` yazmak
#:   da "bir kez oku" sağlardı — ama import'u YAN ETKİLİ yapardı: dosyayı import eden
#:   herkes, config'e ihtiyacı olmasa bile .env okumaya ve eksikse çökmeye mecbur kalırdı.
#:   lru_cache ile maliyet İLK ÇAĞRIYA ertelenir. (docs/notes/18)
@lru_cache(maxsize=1)
def load_config() -> Config:
    """Read, validate and cache configuration, failing loudly if anything is missing."""
    #: ORTAM DEĞİŞKENİ (environment variable) NEDİR:
    #:   İşletim sisteminin her SÜRECE verdiği bir isim->metin sözlüğü. Bir dosya
    #:   değildir, RAM'de yaşar ve süreç ölünce kaybolur. Bir süreç başlattığında
    #:   çocuk süreç ebeveyninin kopyasını devralır — bu yüzden `export X=1` sonrası
    #:   çalıştırdığın python X'i görür, ama başka bir terminal görmez.
    #:   Python'da bu sözlük os.environ'dur; DEĞERLERİ HER ZAMAN str'dir (int yok).
    #:
    #: NEDEN SIRLAR BURADA DURUR: dosyaya yazılmadığı için yanlışlıkla git'e giremez,
    #:   ve aynı kod farklı ortamlarda (laptop / CI / Lambda) DEĞİŞMEDEN çalışır.
    #:   12-factor app'in III. maddesi budur (gerçek bir yayınlanmış ilke, benim görüşüm değil).
    #:
    #: .env DOSYASININ ROLÜ: ortam değişkenlerini elle export etmek zahmetlidir;
    #:   .env yalnızca GELİŞTİRME KOLAYLIĞIDIR. Üretimde .env yoktur — Lambda'da
    #:   değişkenler konsoldan/IaC'den gelir. Kod bu farkı bilmez, ikisini de aynı görür.
    #:
    #: find_dotenv(): bulunduğun dizinden başlayıp YUKARI doğru .env arar. Bulursa
    #:   tam yolu, bulamazsa BOŞ STRING döndürür — exception fırlatmaz. Bu yüzden
    #:   dönüşü if ile kontrol ediyoruz (boş string falsy'dir).
    #:   Yukarı arama önemli: kodu repo kökünden de src/ içinden de çalıştırsan bulur.
    dotenv_path = find_dotenv()
    if dotenv_path:
        # override=False keeps real environment variables winning: Lambda has no .env file
        #: load_dotenv: dosyadaki satırları os.environ'a yazar.
        #: override=False -> zaten TANIMLI olan bir değişkenin üstüne YAZMAZ.
        #: Yani gerçek ortam dosyayı yener. Doğru öncelik budur: Lambda'da .env yok,
        #: ama CI'da hem .env hem gerçek değişken bulunabilir; kazanan gerçek olmalı.
        #: override=True yazsaydın, üretimdeki gerçek anahtarın üstüne yanlışlıkla
        #: repoya sızmış bir .env'in değeri yazılabilirdi. Sessiz ve tehlikeli.
        load_dotenv(dotenv_path, override=False)
        #: Neden f-string değil "%s" + argüman: logger.debug ÖNCE seviyeye bakar.
        #: Mesaj yayınlanmayacaksa metin hiç birleştirilmez (tembel formatlama).
        #: Ayrıca log toplama araçları şablonu sabit olan satırları GRUPLAYABİLİR;
        #: f-string her satırı benzersiz yapar ve gruplama bozulur. ruff kuralı: G004.
        logger.debug("loaded environment file %s", dotenv_path)
    else:
        logger.debug("no .env file found, using the process environment only")

    #: os.environ.get(name, "") — sözlükten oku, YOKSA "" döndür.
    #:   os.environ[name] yazsaydık ilk eksik değişkende KeyError ile dururduk ve
    #:   kullanıcı hataları teker teker görürdü. Burada eksikleri toplamak istiyoruz.
    #: .strip() — .env'den gelen görünmez boşluk ve satır sonu burada temizlenir.
    #:   "LASTFM_API_KEY=abc " satırındaki sondaki boşluk, temizlenmezse imzayı bozar
    #:   ve API 403 döner; sebebi bulması saatler süren bir hatadır.
    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENV_VARS}
    #: Eksikleri TOPLA, sonra bir kere patla. İlk eksikte raise etseydik, üç değişkeni
    #: eksik olan kullanıcı programı üç kez çalıştırmak zorunda kalırdı.
    #: `if not value` — boş string falsy'dir; len(value) == 0 yazmak gürültüdür.
    missing = [name for name, value in values.items() if not value]
    if missing:
        #: Yan yana yazılan iki string literal DERLEME ANINDA birleşir; + gerekmez.
        #: Mesaj hem NEYİN eksik olduğunu hem NE YAPILACAĞINI söylüyor. İyi hata
        #: mesajının ölçüsü budur: okuyan kişi kodu açmadan sorunu çözebilmeli.
        #: logger.error DEĞİL raise: bu noktada logging henüz kurulmamış olabilir,
        #: mesaj hiçbir yere düşmez. Exception'ın gitmeyeceği yer yoktur.
        raise ConfigError(
            f"Missing or empty environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

    #: missing kontrolünü geçtiğimiz için values["LASTFM_API_KEY"] güvenli: anahtarın
    #: var ve dolu olduğunu bir satır önce kanıtladık.
    #: İsim eşlemesi ELLE yapılıyor (env adı -> alan adı). Bir değişkende sorun yok;
    #: on değişkende bu on satır olur ve her yeni alan iki yerde değişiklik ister.
    #: pydantic-settings tam olarak orada devreye girer (docs/notes/18 §6).
    config = Config(lastfm_api_key=values["LASTFM_API_KEY"])
    #: Bir Config nesnesini loglamak GÜVENLİ, çünkü metin hâli maskeli (0.3'teki zincir).
    #: Kod incelemesinde "config loglanmış" görünce alarma geçilir; buradaki cevap
    #: satır 22'deki repr=False ve satır 37'deki elle yazılmış __repr__'dir.
    logger.debug("configuration loaded: %s", config)  # masked repr, safe to log
    return config
#:
#: ============================================================================
#: BURADA OLMAYANLAR VE NE ZAMAN GELECEKLERİ
#: ============================================================================
#: APP_ENV + LOG_LEVEL ve setup_logging()  -> P2.1
#: HTTP timeout + retry ayarları           -> P2.1
#: AWS_REGION + bucket adları              -> P2.2
#: secret store (Secrets Manager/SSM)      -> P3
#: pydantic-settings'e geçiş               -> alan sayısı elle eşlemeyi zorlaştırınca
#: Bugün eklemek, hiçbir kod dalının okumadığı alanlar üretirdi.
#: GERÇEKTEN EKSİK OLAN TEK ŞEY: test (P2.4) — ve o test cache_clear() çağırmak zorunda.

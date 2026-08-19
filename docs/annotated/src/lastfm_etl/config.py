#: Yorumlu ayna. "#:" ile başlayan satırlar gerçek dosyada yoktur; kalan her karakter
#: src/lastfm_etl/config.py ile birebir aynıdır. Sapma kontrolü:
#:   grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/config.py | diff - src/lastfm_etl/config.py
#: Tasarım gerekçeleri: docs/notes/18 · dil araçları ve kanıt komutları: docs/notes/19
#:
#: Burada olmayanlar ve ne zaman gelecekleri: APP_ENV ile LOG_LEVEL P2.1'de, HTTP timeout
#: ve retry P2.1'de, AWS_REGION ile bucket adları P2.2'de, secret store P3'te. Bugün
#: eklemek hiçbir kodun okumadığı alanlar üretirdi. Gerçekten eksik tek şey test: P2.4.
"""Application configuration, loaded once from the environment."""

#: PEP 8 import sırası: stdlib, üçüncü parti, yerel — aralarında boş satır (ruff I001).
#: dotenv ayrı grupta çünkü dışarıdan gelen tek bağımlılık; bakışta görünmesi gerekir.
import logging
import os
from dataclasses import dataclass, fields
from functools import lru_cache
from typing import Final

from dotenv import find_dotenv, load_dotenv

# Module-level logger: no setup, no side effect. The application configures handlers.
#: getLogger bir kayıt defteri araması: aynı isim aynı nesneyi verir, import anında güvenli.
#: Handler'ı yok, o yüzden sessiz. Logging'i uygulama kurar, kütüphane değil.
logger = logging.getLogger(__name__)

# Every name here must be present and non-empty before the pipeline may start
#: Final çalışma zamanında bir şeyi kilitlemez; yalnızca mypy'ye "yeniden atama yok" der.
#: Tuple'ı sondaki virgül yapar: ("X") bir string'tir, ("X",) tek elemanlı tuple.
#: list değil tuple, çünkü bu bir sabit — yanlışlıkla append edilemesin.
REQUIRED_ENV_VARS: Final[tuple[str, ...]] = ("LASTFM_API_KEY",)


#: Kendi hata tipimiz, çağıran taraf "except ConfigError" yazabilsin diye. RuntimeError
#: seçildi çünkü sorun argümanda değil ortamda. Gövde docstring olduğu için pass gerekmez.
class ConfigError(RuntimeError):
    """Raised when required configuration is missing, empty or invalid."""


#: frozen: config başlangıçta alınan bir ölçümdür, değişken değil; atama denemesi patlar.
#: slots: __dict__ yok, alan adını yanlış yazınca sessizce yeni bir alan oluşmaz.
#: repr=False: üretilen repr bütün alanları basar, yani key'i loga dökerdi (satır 37).
@dataclass(frozen=True, slots=True, repr=False)
class Config:
    """Validated runtime configuration.

    Frozen because configuration is a reading taken at startup, not a variable.
    """

#: Sadece annotation. Değer yazsan varsayılan olurdu; annotation'sız yazsan alan olmazdı.
    lastfm_api_key: str

#: dataclass'ın ürettiği __init__ alanları atadıktan sonra bunu kendisi çağırır.
#: Burada hata fırlatmak, geçersiz bir Config nesnesinin hiç doğmaması demektir.
#: load_config yanlış ortamdan korur; burası kodun kendisinden korur, testler dahil.
    def __post_init__(self) -> None:
        # Backstop invariant: no code path, not even a test, may build an invalid Config
#:        #: fields(self) alan tanımlarını verir, getattr ise adı string olan özniteliği okur.
#:        #: Tek alanda fazla iş gibi görünür; ikinci alan eklendiğinde kontrol kendiliğinden kapsar.
#:        #: Dikkat: .strip() str varsayar — ilk int alan eklendiğinde burası AttributeError verir.
        blank = [f.name for f in fields(self) if not getattr(self, f.name).strip()]
        if blank:
            raise ConfigError(f"Config fields must not be empty: {', '.join(blank)}")

#:    #: __str__ tanımlı değil, str() buraya düşer; satır 62'deki log da maskeli çıkar.
#:    #: [-4:] taşmaz: dört karakterden kısa string'te hata yerine olanı döndürür.
    def __repr__(self) -> str:
        # The generated dataclass repr prints every field; this one must never leak the key
        return f"Config(lastfm_api_key='***{self.lastfm_api_key[-4:]}')"


#: Argümansız fonksiyon + cache: gövde bir kez çalışır, her çağrı aynı nesneyi döndürür.
#: Testte ortamı değiştirince eskisi dönmeye devam eder; load_config.cache_clear() gerekir.
#: Modül seviyesinde "config = load_config()" yazmak import'u yan etkili yapardı.
@lru_cache(maxsize=1)
def load_config() -> Config:
    """Read, validate and cache configuration, failing loudly if anything is missing."""
#:    #: find_dotenv yukarı doğru arar; bulamazsa boş string döndürür, hata fırlatmaz.
    dotenv_path = find_dotenv()
    if dotenv_path:
        # override=False keeps real environment variables winning: Lambda has no .env file
#:        #: override=False: gerçek ortam değişkeni dosyayı yener. Lambda'da .env yoktur.
        load_dotenv(dotenv_path, override=False)
#:        #: %s + argüman: metin yalnızca kayıt yayınlanırsa birleşir, log şablonu sabit kalır.
#:        #: f-string yazarsan her satır benzersizleşir ve log toplama gruplayamaz (ruff G004).
        logger.debug("loaded environment file %s", dotenv_path)
    else:
        logger.debug("no .env file found, using the process environment only")

#:    #: .get(name, "") yoksa boş döner; os.environ[name] ilk eksikte KeyError ile dururdu.
#:    #: strip: .env'den gelen görünmez boşluk ve satır sonu burada temizlenir.
    values = {name: os.environ.get(name, "").strip() for name in REQUIRED_ENV_VARS}
#:    #: Eksikleri topla, bir kere patla. İlk eksikte raise etmek kullanıcıyı üç tur döndürür.
    missing = [name for name, value in values.items() if not value]
    if missing:
#:        #: Bitişik iki literal derleme anında birleşir. Mesaj ne yapılacağını da söylüyor.
#:        #: logger.error değil raise: bu noktada logging kurulmamış olabilir, mesaj kaybolur.
        raise ConfigError(
            f"Missing or empty environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

#:    #: missing kontrolü geçtiği için [] güvenli. İsim eşlemesi elle yapılıyor; on değişkende
#:    #: bu on satır olur, pydantic-settings tam olarak orada devreye girer (notes/18 §6).
    config = Config(lastfm_api_key=values["LASTFM_API_KEY"])
#:    #: Loglamak güvenli, çünkü repr maskeli: satır 22'deki repr=False + satır 37.
    logger.debug("configuration loaded: %s", config)  # masked repr, safe to log
    return config

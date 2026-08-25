#: ============================================================================
#: YORUMLU AYNA - src/lastfm_etl/extract/api.py
#: ============================================================================
#: "#:" ile baslayan her satir aciklamadir ve gercek dosyada YOKTUR.
#: Kalan her karakter src/lastfm_etl/extract/api.py ile birebir aynidir. Sapma kontrolu:
#:   grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/extract/api.py | diff - src/lastfm_etl/extract/api.py
#: Cikti bossa ayna guncel.
#:
#: Yazim sozlesmesi (docs/annotated/README.md):
#:   NE    - bu sozdizimi/nesne aslinda nedir, Python bununla ne yapar
#:   KANIT - iddiayi calistirarak dogrulayan komut
#:   BIZDE - bizim kodda tam olarak neyi degistiriyor
#:
#: Bu dosyayi OKUMAK yetmez. KANIT komutlarini terminalde calistir. Calistirilmayan
#: aciklama, okunmus sayilmaz - cunku okurken beyin "mantikli" der ve ogrendigini saNIR.
#:
#: Tasarim gerekceleri (retry taksonomisi, hata yolu): docs/notes/17
#: Paket/__init__ konulari: docs/notes/22
#: Sayfalama ve dongu sonlandirma: docs/notes/23 - generator/yield: docs/notes/24
#: Sayfalamanin nereye ait oldugu karari: docs/adr/0015
#:
#: ============================================================================
#: BOLUM 0 - ONCE SU YEDI KAVRAM
#: ============================================================================
#: Asagidaki kod bu yedisini bilmeden okunmaz. Hicbiri bu dosyaya ozel degil.
#:
#: ----------------------------------------------------------------------------
#: 0.1 - EXCEPTION NEDIR, raise NE YAPAR
#: ----------------------------------------------------------------------------
#: NE: Exception bir NESNEDIR. Ozel bir dil yapisi degil - Exception sinifindan
#:     tureyen siradan bir sinifin ornegidir. Ozel olan sey nesnenin kendisi degil,
#:     `raise` ile ne oldugudur.
#:
#:     `raise X("mesaj")` su demektir: "bu fonksiyonu BURADA birak, hicbir sey
#:     dondurme, ve X nesnesini cagirana firlat." Fonksiyon o satirdan sonra devam
#:     etmez - `return` gibi, ama deger yerine hata tasir.
#:
#:     Cagiran onu yakalamazsa, o da kendi cagiranina firlatir. Zincirin en ustune
#:     kadar kimse yakalamazsa program traceback basip olur.
#:
#: KANIT:
#:   uv run python -c "
#:   class Bos(Exception): pass
#:   print(issubclass(Bos, Exception))     # True  -> siradan bir sinif
#:   e = Bos('selam')
#:   print(type(e), e.args, str(e))        # nesne, tuple, mesaj
#:   "
#:
#: BIZDE: LastfmError, LastfmAPIError, LastfmTransientError ucu de bu dosyada
#:     tanimli siradan siniflar. Hicbir sihir yok; degerli olan sey isimlendirme.
#:
#: ----------------------------------------------------------------------------
#: 0.2 - except NASIL ESLESIR: KALITIM ZINCIRI
#: ----------------------------------------------------------------------------
#: NE: `except X` sadece tam X'i degil, X'TEN TUREYEN her seyi yakalar. Eslesme
#:     kurali `isinstance(hata, X)`.
#:
#:     Bizim hiyerarsi:
#:         Exception
#:           +-- LastfmError                 <- hepsinin atasi
#:                 +-- LastfmAPIError        <- kalici, API hata belgesi dondu
#:                 +-- LastfmTransientError  <- gecici, tekrar denenebilir
#:
#:     Sonuc: `except LastfmError` ucunu de yakalar. `except LastfmAPIError` sadece
#:     birini. Cagiran ne kadar detay istiyorsa o kadar asagi iner.
#:
#:     Bu yuzden exception hiyerarsisi bir MODULUN ARAYUZUDUR. Fonksiyon imzasi
#:     "ne donerim"i, exception agaci "nasil basarisiz olurum"u anlatir.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract import LastfmError, LastfmAPIError, LastfmTransientError
#:   e = LastfmAPIError(10, 'Invalid API key')
#:   print(isinstance(e, LastfmAPIError), isinstance(e, LastfmError), isinstance(e, Exception))
#:   print(LastfmTransientError.__mro__)   # kalitim zinciri, soldan saga
#:   "
#:
#: BIZDE: tenacity yalnizca LastfmTransientError'i retry eder. Eger onu
#:     LastfmError'in DEGIL de LastfmAPIError'in altina koysaydik, kalici hatalar da
#:     retry edilirdi - sessizce, sadece kalitim yanlis oldugu icin.
#:
#: ----------------------------------------------------------------------------
#: 0.3 - try / except / as / from
#: ----------------------------------------------------------------------------
#: NE: `try:` blogu "burada hata cikabilir" der. `except X as exc:` cikan hata X ile
#:     eslesirse calisir ve hata nesnesini `exc` adiyla verir.
#:
#:     `raise Y(...) from exc` = "Y'yi firlatiyorum, SEBEBI exc". Traceback'te:
#:         from exc VARSA  -> "The above exception was the direct cause of..."
#:         from exc YOKSA  -> "During handling of the above exception, another
#:                             exception occurred" (yani: kaza gibi gorunur)
#:     Ikisi de asil hatayi gosterir, ama ilki "bunu ben bilerek cevirdim" der.
#:
#:     KRITIK KURAL: try blogu MUMKUN OLDUGUNCA DAR olmali. Genis bir try, icindeki
#:     alakasiz bir bug'i da yakalar ve yanlis etiketler.
#:
#: KANIT:
#:   uv run python -c "
#:   try:
#:       try:
#:           int('abc')
#:       except ValueError as exc:
#:           raise RuntimeError('cevirdim') from exc
#:   except RuntimeError as e:
#:       print('sebep:', repr(e.__cause__))       # from exc bunu doldurur
#:       print('baglam:', repr(e.__context__))
#:   "
#:
#: BIZDE: `except requests.RequestException as exc: raise LastfmTransientError(...)
#:     from exc`. Alt katmanin hatasini (requests) kendi domain hatamiza ceviriyoruz.
#:     Cagiran artik requests'i tanimak zorunda degil - ama traceback'te asil
#:     ConnectTimeout hala duruyor.
#:
#: ----------------------------------------------------------------------------
#: 0.4 - DECORATOR (@) NEDIR
#: ----------------------------------------------------------------------------
#: NE: Python'da fonksiyonlar nesnedir: degiskene atanir, parametre olarak gecer,
#:     baska bir fonksiyon tarafindan DONDURULUR.
#:
#:     Decorator tam olarak bu: fonksiyonu alip yerine baska bir fonksiyon koyan bir
#:     fonksiyon. Su iki yazim BIREBIR ayni seydir:
#:
#:         @retry(...)              def _request(...): ...
#:         def _request(...): ...   _request = retry(...)(_request)
#:
#:     Yani `_request` adi artik senin yazdigin fonksiyona degil, tenacity'nin
#:     urettigi SARMALAYICIYA baglidir. Sarmalayici cagrildiginda seninkini bir
#:     dongu icinde cagirir, hata gelirse bekler ve tekrar cagirir.
#:
#: KANIT:
#:   uv run python -c "
#:   def sayan(f):
#:       def sarmal(*a, **k):
#:           print('cagriliyor:', f.__name__)
#:           return f(*a, **k)
#:       return sarmal
#:   @sayan
#:   def topla(a, b): return a + b
#:   print(topla(2, 3))
#:   print(topla.__name__)   # 'sarmal' -> isim artik sarmalayiciya bagli
#:   "
#:
#: BIZDE: @retry(...) tenacity'nin sarmalayicisidir. Gozle gorunmeyen sonucu su:
#:     _request'in govdesi BIR CAGRIDA 4 KEZ calisabilir. Govdeye kalici bir yan
#:     etki (dosya yazma, sayac artirma) koyarsan 4 kez olur.
#:
#: ----------------------------------------------------------------------------
#: 0.5 - KEYWORD-ONLY PARAMETRE: imzadaki tek basina *
#: ----------------------------------------------------------------------------
#: NE: Imzada tek basina duran `*`, kendisinden SONRAKI parametrelerin yalnizca
#:     isimle gecilebilecegini soyler.
#:
#:         def f(a, *, b): ...
#:         f(1, 2)      -> TypeError
#:         f(1, b=2)    -> calisir
#:
#:     Neden: (1) cagri yeri okunur olur - fetch_top_tracks(config, 100, 1) hangisi
#:     limit hangisi page belli degil; (2) pozisyonel parametre donmus bir
#:     sozlesmedir, sirasini degistirdigin gun butun cagrilar SESSIZCE bozulur.
#:
#:     Kalip (benim gorusum, ama yaygin; sozdizimi PEP 3102): fonksiyonun UZERINDE
#:     CALISTIGI seyler pozisyonel, AYAR olanlar keyword-only.
#:
#: KANIT:
#:   uv run python -c "
#:   def f(a, *, b): return a, b
#:   print(f(1, b=2))
#:   try: f(1, 2)
#:   except TypeError as e: print('TypeError:', e)
#:   "
#:
#: BIZDE: timeout, limit, page, session hepsi `*`'in sagindadir. Yarin araya bir
#:     parametre eklesek hicbir cagri kirilmaz.
#:
#: ----------------------------------------------------------------------------
#: 0.6 - frozenset VE in OPERATORU
#: ----------------------------------------------------------------------------
#: NE: set = sirasiz, tekrarsiz koleksiyon. frozenset = degistirilemez set.
#:     `x in kume` bir HASH aramasidir: kume 5 elemanli da olsa 5 milyon elemanli da
#:     olsa sabit surede biter. Liste olsaydi bastan sona taranirdi.
#:
#:     Asil sebep hiz degil NIYET: frozenset "bu kume calisma zamaninda degismeyecek"
#:     der ve yanlislikla .add() cagirmayi imkansiz kilar.
#:
#:     TUZAK: `in` tip donusumu yapmaz. "29" in {29} -> False. Sessizce.
#:
#: KANIT:
#:   uv run python -c "
#:   k = frozenset({8, 11, 16, 29})
#:   print(29 in k, '29' in k)          # True False  <- tuzak burada
#:   try: k.add(1)
#:   except AttributeError as e: print('degistirilemez:', e)
#:   "
#:
#: BIZDE: RETRYABLE_ERROR_CODES bir frozenset[int]. Bu yuzden kodda
#:     `code = int(payload["error"])` var: API bir gun "29" (string) dondurse,
#:     donusum olmadan retry SESSIZCE calismazdi.
#:
#: ----------------------------------------------------------------------------
#: 0.7 - requests: Session VE Response
#: ----------------------------------------------------------------------------
#: NE: `requests.Session()` acilan TCP baglantisini ve TLS el sikismasini saklar;
#:     ayni sunucuya ikinci istek el sikismayi tekrarlamaz. Tek istek atacaksan farki
#:     yok, 10 sayfa cekeceksen belirgin.
#:
#:     `session.get(...)` bir Response nesnesi doner. Onemli uyeleri:
#:         .status_code  -> int, HTTP durum kodu
#:         .text         -> govde, str
#:         .json()       -> govdeyi JSON olarak coz; cozemezse ValueError firlatir
#:         .raise_for_status() -> status 4xx/5xx ise requests.HTTPError firlatir
#:
#:     Bu dosyada raise_for_status() BILEREK KULLANILMIYOR. Iki sebep: (1) Last.fm
#:     gecersiz API key'e HTTP 200 doner, yani raise_for_status onu hic gormez;
#:     (2) firlattigi HTTPError bizim tipimiz degil, tenacity onu retry etmez.
#:
#: KANIT:
#:   uv run python -c "
#:   import requests
#:   r = requests.get('http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=bozuk&format=json', timeout=5)
#:   print(r.status_code)      # 403 veya 200 - Last.fm surumune gore degisir
#:   print(r.json())           # {'message': ..., 'error': 10}  <- asil hata GOVDEDE
#:   "
#:
#: BIZDE: govde status'tan once okunur. Sira bu dosyanin en onemli tasarim karari.
#:
#: ============================================================================
#: BOLUM 1 - SATIR SATIR
#: ============================================================================
#:
"""Fetch chart data from the Last.fm API.

This module owns one thing: turning a Last.fm API method call into either a raw JSON
payload or a typed exception. It does not reshape, flatten or persist anything — what it
returns is what the API sent, so the raw layer (P2.2) can store it untouched.
"""

#: ----------------------------------------------------------------------------
#: NE: Bu satir, dosyadaki BUTUN type hint'lerin calisma zamaninda degerlendirilmesini
#:     kapatir; hepsi string olarak saklanir (PEP 563).
#:
#:     Pratik faydasi: henuz tanimlanmamis veya import edilmemis tipleri hint olarak
#:     yazabilirsin, ve `X | None` gibi yeni sozdizimini eski Python'larda da
#:     kullanabilirsin.
#:
#:     Sadece ANNOTATION'lari etkiler. Kodun geri kalani aynen calisir.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract import api
#:   print(api.fetch_top_tracks.__annotations__['session'])   # string olarak duruyor
#:   "
#:
#: BIZDE: `session: requests.Session | None = None` hint'i bu satir sayesinde
#:     calisma zamaninda hic degerlendirilmiyor - maliyeti sifir.
from __future__ import annotations

import logging
from typing import Any, Final

#: ----------------------------------------------------------------------------
#: NE: PEP 8 import sirasi ucludur ve aralarinda bos satir olur:
#:         1. standart kutuphane   (logging, typing)
#:         2. ucuncu parti         (requests, tenacity)
#:         3. kendi paketimiz      (lastfm_etl.config)
#:     Bu bir stil kurali degil, bir OKUMA kolayligi: bir dosyanin dis bagimliligini
#:     tek bakista gormek icin.
#:
#:     tenacity'den ithal edilen bes isim birer FONKSIYON, birer strateji parcasi:
#:         retry_if_exception_type -> hangi hata retry edilir
#:         stop_after_attempt      -> ne zaman vazgecilir
#:         wait_exponential_jitter -> denemeler arasi ne kadar beklenir
#:         before_sleep_log        -> her beklemeden once ne loglanir
#:         retry                   -> yukaridakileri birlestiren decorator
#:
#: BIZDE: parcali olmasinin sebebi: tenacity retry'in NASIL'ini cozer. NE ZAMAN
#:     sorusu (hangi hata gecicidir) hala bizim isimiz - RETRYABLE_ERROR_CODES.
import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from lastfm_etl.config import Config

#: ----------------------------------------------------------------------------
#: NE: getLogger(__name__) bu modulun adiyla ("lastfm_etl.extract.api") bir logger
#:     alir. Handler kurmaz, seviye ayarlamaz, HICBIR yan etkisi yoktur.
#:
#:     Neden __name__: logger isimleri noktayla hiyerarsi kurar. Uygulama
#:     "lastfm_etl.extract" seviyesini DEBUG yapinca bu modul de otomatik DEBUG olur.
#:     Sabit bir isim yazsaydin o hiyerarsi kaybolurdu.
#:
#:     KURAL: kutuphane/modul kodu logger ALIR, logging'i YAPILANDIRMAZ.
#:     basicConfig() cagirmak uygulamanin (veya Lambda handler'inin) isidir.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract import api
#:   print(api.logger.name, api.logger.handlers)   # isim dolu, handler listesi bos
#:   "
logger = logging.getLogger(__name__)

#: ----------------------------------------------------------------------------
#: NE: `Final` bir type checker isaretidir: "bu isim bir daha atanmayacak".
#:     CALISMA ZAMANINDA HICBIR SEYI KILITLEMEZ - degistirmeyi denersen Python
#:     itiraz etmez, sadece mypy uyarir.
#:
#:     Deger yazilmadigi icin (Final = "..." seklinde, Final[str] degil) tip
#:     cikarimla str olur.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract import api
#:   api.BASE_URL = 'degistirdim'; print(api.BASE_URL)   # calisir! Final koruma degil
#:   "
#:
#: BIZDE: TOP_TRACKS_METHOD ayri bir sabit, cunku ayni string uc yere gidiyor:
#:     istegin params'ina, log satirina, ve her exception mesajina. Ucunden birinde
#:     yapilacak yazim hatasi SESSIZ olurdu - istek yanlis metoda gider, log dogru
#:     metodu yazar.
BASE_URL: Final = "http://ws.audioscrobbler.com/2.0/"
TOP_TRACKS_METHOD: Final = "chart.getTopTracks"

# (connect, read): a connect timeout means the host never answered, a read timeout means
# it answered and then went quiet. Never omit — without it requests waits forever.
#: ----------------------------------------------------------------------------
#: NE: requests'in timeout parametresi bir sayi da alir, iki elemanli bir tuple da.
#:     Tuple verirsen (connect, read) olarak ayrilir:
#:         connect - sunucuya baglanma suresi. Asilirsa host hic cevap vermedi.
#:         read    - baglandiktan sonra iki veri parcasi arasi bekleme suresi.
#:
#:     3.05 rakami keyfi degil: TCP yeniden iletim penceresi 3 saniyenin katlarinda
#:     calisir, uzerine kucuk bir pay konur. requests dokumaninin kendi onerisi.
#:
#:     HIC TIMEOUT VERMEZSEN requests SONSUZA KADAR BEKLER. Bu, Lambda'da su demek:
#:     fonksiyon kendi timeout'unda oldurulur, log'da hicbir aciklayici satir olmaz.
#:
#: BIZDE: `10.0` degeri simdilik tahmindir. PROGRESS.md 1.8'de "20 ardisik istekle
#:     gecikme olcumu" diye bekleyen olcum tam olarak bu sayiyi gercek veriye
#:     baglamak icindir. Tahminle timeout koymak yaygin ve yanlistir.
DEFAULT_TIMEOUT: Final[tuple[float, float]] = (3.05, 10.0)

#: ----------------------------------------------------------------------------
#: NE: Bu iki sayi bir BUTCEDIR. 4 deneme = 1 asil + 3 tekrar. Ustel backoff ile
#:     beklemeler yaklasik 1s, 2s, 4s (+ jitter), tavan 30s.
#:
#:     Toplam en kotu senaryo ~7-10 saniye + istek sureleri. Lambda timeout'unun
#:     (ROADMAP P3.1: 1 dakika) altinda kalmasi gerekir, yoksa retry'in son denemesi
#:     hic calismadan fonksiyon oldurulur.
#:
#:     JUNIOR TUZAGI: retry sayisini "ne olur ne olmaz" diye 10 yapmak. Sonuc:
#:     Lambda 60 saniyede olur, retry hicbir zaman tamamlanmaz, ve loglarda sebep
#:     gorunmez - fonksiyon sadece "timed out" der.
MAX_ATTEMPTS: Final = 4
MAX_BACKOFF_SECONDS: Final = 30

# Last.fm reports its real failure in the body, not the status line. Only these codes
# describe a condition that may clear on its own; 26 (suspended key) is deliberately
# absent, because retrying a suspended key makes it worse.
#: ----------------------------------------------------------------------------
#: NE: Bu kume bir TAKSONOMIDIR - retry'in "ne zaman" sorusunun cevabi, ve tenacity
#:     bunu bizim yerimize cozemez.
#:
#:     Last.fm hata kodlari (dokumandan):
#:         8  operation failed        -> gecici, backend hatasi
#:         11 service offline         -> gecici, bakim
#:         16 temporary error         -> gecici, adi ustunde
#:         29 rate limit exceeded     -> gecici, ama beklemek SART
#:         ---
#:         2  invalid service         -> kalici, yanlis istek
#:         3  invalid method          -> kalici, yanlis metod adi
#:         10 invalid API key         -> kalici, key yanlis
#:         26 suspended API key       -> KALICI VE BILEREK DISARIDA
#:
#:     26'nin disarida olmasi bir karardir, unutkanlik degil: askiya alinmis bir
#:     anahtarla 4 kez daha denemek durumu iyilestirmez, kotulestirir.
#:
#:     RETRYABLE_STATUS_CODES (429, 500, 502, 503, 504) ayni mantigin HTTP tarafi.
#:     429 = too many requests, 5xx = sunucu tarafi. 4xx'in geri kalani (400, 401,
#:     403, 404) senin istegin yanlis demektir - tekrar denemek ayni yanlisi
#:     tekrarlamaktir.
#:
#: KANIT (fixture'lardan, aga cikmadan):
#:   uv run python -c "
#:   import json
#:   from lastfm_etl.extract.api import RETRYABLE_ERROR_CODES
#:   d = json.load(open('tests/fixtures/lastfm/error_10_invalid_api_key.json'))
#:   print(d['error'], d['error'] in RETRYABLE_ERROR_CODES)   # 10 False -> retry YOK
#:   "
RETRYABLE_ERROR_CODES: Final[frozenset[int]] = frozenset({8, 11, 16, 29})

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})

#: ----------------------------------------------------------------------------
#: NE: Uc sabit, ucu de bir sayi degil bir KARAR tasiyor. Degerli olan sayinin kendisi
#:     degil, neden o sayi oldugu - o yuzden yorumlar "ne" degil "neden" yaziyor.
#:
#:     DEFAULT_PAGE_SIZE < TARGET_TRACK_COUNT olmasi kasitli. Esit olsalardi dongu her
#:     kosuda TAM BIR tur donerdi: yazdigimiz sayfalama kodu uretimde hic sinanmaz,
#:     gercekten gerektigi gun (sunucu 50 yerine 30 dondurdugunde) ILK KEZ calisirdi.
#:     Ilk kez calisan kod calismaz.
#:
#:     MAX_PAGES bir "olmamasi gereken" sinirdir; baglamasi beklenmez. Amaci dogru sonuc
#:     uretmek degil, YANLIS DURUMDA DURMAK. Acik uclu her dongude boyle bir tavan
#:     bulunur: prod'da seni uyandiran sey dongunun yanlis cevap vermesi degil, hic
#:     donmemesidir. Lambda'da bu, timeout'a kadar para yakip hicbir sey yazmadan olmek.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract.api import DEFAULT_PAGE_SIZE, TARGET_TRACK_COUNT, MAX_PAGES
#:   print(DEFAULT_PAGE_SIZE < TARGET_TRACK_COUNT)  # True -> dongu her kosuda >=2 tur
#:   print(MAX_PAGES * DEFAULT_PAGE_SIZE)           # 500  -> tavanin kapsadigi kayit
#:   "
#:
#: BIZDE: fetch_top_tracks_pages ucunu de varsayilan olarak alir. Cagiran hicbirini
#:     bilmek zorunda degil; test uc'unu de override edebilir (KANIT 3, en altta).
#:     Konu notu: docs/notes/23
# Deliberately below TARGET_TRACK_COUNT so the pagination path runs on every
# execution. A loop that makes a single pass is untested code that first runs on the
# day it matters.
DEFAULT_PAGE_SIZE: Final = 50
TARGET_TRACK_COUNT: Final = 100

# Never expected to bind: 100 tracks at 50 a page is two calls. It exists so a server
# that answers without making progress ends the loop instead of the Lambda timeout.
MAX_PAGES: Final = 10


#: ----------------------------------------------------------------------------
#: NE: Uc sinif, uc farkli SORU cevapliyor - govde yok, sadece docstring var.
#:     Bir exception sinifinin govdesi cogu zaman bostur; degerli olan sey TIPTIR.
#:
#:         LastfmError            "bu modulden bir hata geldi"        -> genel yakalama
#:         LastfmAPIError         "API cevap verdi, cevap hataydi"    -> kalici
#:         LastfmTransientError   "tekrar denemeye deger"             -> tenacity bunu izler
#:
#:     Neden `pass` yerine docstring: ikisi de govdeyi doldurur, ama docstring ayni
#:     zamanda `help()` ve IDE ipucu uretir. Bedava kazanc.
#:
#: BIZDE: Cagiran (P2.2, sonra Lambda) `except LastfmAPIError` yazip koda gore karar
#:     verebilir; hicbiri umurunda degilse `except LastfmError` yazip hepsini
#:     yakalar. Iki ayri detay seviyesi, tek agac.
class LastfmError(Exception):
    """Base class for every failure raised by this module."""


class LastfmAPIError(LastfmError):
    """The API answered, and the answer was an error document."""

#: ----------------------------------------------------------------------------
#: NE: Bu tek override edilen metot. Uc is yapiyor:
#:
#:     1. `super().__init__(f"...")` - ust sinifin (Exception) kurucusunu cagirir ve
#:        mesaji ona verir. Exception mesaji orada saklanir; `str(e)` bunu basar.
#:        Bunu ATLARSAN `print(e)` bos satir basar.
#:     2. `self.code = code` - hata kodunu NESNENIN UZERINDE saklar.
#:     3. `self.message = message`
#:
#:     2. adim asil mesele. Kodu mesaj stringinin icine gomup birakirsan, cagiran
#:     onu kullanmak icin metni PARSE etmek zorunda kalir:
#:         if "error 29" in str(e):     <- kirilgan, dile bagli, sessizce bozulur
#:     Ayri bir alan olunca:
#:         if e.code == 29:             <- makine okur
#:
#:     KURAL: hata mesaji INSAN icindir, hata alanlari MAKINE icin.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract import LastfmAPIError
#:   e = LastfmAPIError(10, 'Invalid API key')
#:   print(str(e)); print(e.code, type(e.code))
#:   "
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Last.fm error {code}: {message}")
        self.code = code
        self.message = message


class LastfmTransientError(LastfmError):
    """A failure that may succeed if the same call is repeated later."""


#: ----------------------------------------------------------------------------
#: NE: Bes parametre, retry davranisinin bes ayri sorusu:
#:
#:     retry=retry_if_exception_type(LastfmTransientError)
#:         HANGI hata tekrar denenir. Tek tip. LastfmAPIError buradan gecmez ve ILK
#:         denemede yukari kacar - yanlis API key dorduncu denemede dogru olmaz.
#:
#:     stop=stop_after_attempt(MAX_ATTEMPTS)
#:         NE ZAMAN vazgecilir. 4 = 1 asil + 3 tekrar.
#:
#:     wait=wait_exponential_jitter(initial=1, max=MAX_BACKOFF_SECONDS)
#:         NE KADAR beklenir. Formul: min(initial * 2**n + uniform(0, jitter), max).
#:         "jitter" = rastgele pay. Olmasaydi ayni anda hata alan butun istemciler
#:         ayni anda tekrar denerdi ve sunucuyu ayni anda tekrar vururdu (thundering
#:         herd). Rastgelelik surunun dagilmasini saglar.
#:
#:     before_sleep=before_sleep_log(logger, logging.WARNING)
#:         Her beklemeden ONCE bir WARNING satiri yazar. Bu, retry'in gorunur
#:         olmasidir: retry sessiz olursa "yavas ama calisiyor" gorunur ve altindaki
#:         arizayi aylarca gizler.
#:
#:     reraise=True
#:         Bu OLMASAYDI son hata tenacity.RetryError icine sarilirdi ve cagiran,
#:         karar vermek icin gereken Last.fm hata kodunu kaybederdi.
#:
#: KANIT (retry'in gorunur oldugunu ispat):
#:   uv run python -c "
#:   import logging; logging.basicConfig(level=logging.WARNING)
#:   from tenacity import retry, stop_after_attempt, wait_exponential_jitter, before_sleep_log
#:   log = logging.getLogger('x')
#:   @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.1, max=1),
#:          before_sleep=before_sleep_log(log, logging.WARNING), reraise=True)
#:   def f(): raise ValueError('hep patlar')
#:   try: f()
#:   except ValueError as e: print('son hata:', e)
#:   "
#:   # Iki WARNING satiri + son hata gorunur. Uc deneme, iki bekleme.
#:
#: BIZDE: Bu decorator yuzunden _request'in govdesi TEK CAGRIDA 4 KEZ calisabilir.
#:     Aklinda tut - P2.2'de S3'e yazma bu fonksiyonun icine KONMAYACAK, tam olarak
#:     bu yuzden.
@retry(
    retry=retry_if_exception_type(LastfmTransientError),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential_jitter(initial=1, max=MAX_BACKOFF_SECONDS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    # Without this the final failure arrives wrapped in RetryError and the caller loses
    # the Last.fm error code it needs to act on.
    reraise=True,
)
def _request(
    session: requests.Session,
    method: str,
    params: dict[str, str],
    *,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Perform one HTTP call and return the decoded payload.

    Raises:
        LastfmTransientError: network failure, or a status/error code worth retrying.
        LastfmAPIError: the API returned a permanent error document.
        LastfmError: the response was not JSON, or carried a bad status and no error
            document.
    """
    try:
#: ----------------------------------------------------------------------------
#: ADIM 1/5 - ISTEK
#: NE: try blogu YALNIZCA bu tek satiri sariyor. Bu bir titizlik degil, dogruluk
#:     meselesi: try genisledikce, icindeki alakasiz bir bug da
#:     requests.RequestException'a benzeyip "ag hatasi" diye etiketlenme riskine
#:     girer - ve sonra uc kez daha tekrar denenir.
#:
#:     KURAL: try blogunu daralttigin kadar dogrudur.
#:
#:     requests.RequestException requests'in butun ag hatalarinin ATASIDIR:
#:     ConnectTimeout, ReadTimeout, ConnectionError, TooManyRedirects hepsi ondan
#:     turer. Tek satirla hepsi kapsanir. (0.2'deki kalitim kurali.)
#:
#: KANIT:
#:   uv run python -c "
#:   import requests
#:   for t in (requests.ConnectTimeout, requests.ReadTimeout, requests.ConnectionError):
#:       print(t.__name__, issubclass(t, requests.RequestException))
#:   "
#:
#: BIZDE (Baris ilk denemesinde soyle yazmisti):
#:       except (LastfmTransientError):
#:           raise
#:     Iki hata birden: (1) session.get() asla LastfmTransientError firlatmaz - o
#:     BIZIM firlatmak ISTEDIGIMIZ tip, requests'in firlattigi tip degil. Bu except
#:     hicbir zaman tetiklenmez. (2) ciplak `raise` yakalanani aynen tekrar firlatir,
#:     yani blok hicbir sey yapmaz.
#:
#:     try/except yazmanin amaci TIP CEVIRMEKTIR: alt katmanin hatasi (requests) ->
#:     bizim domain hatamiz (LastfmTransientError). Boylece cagiran requests'i
#:     tanimak zorunda kalmaz.
        response = session.get(BASE_URL, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise LastfmTransientError(f"{method}: request failed: {exc}") from exc

    try:
#: ----------------------------------------------------------------------------
#: ADIM 2/5 - GOVDEYI COZ (STATUS'TAN ONCE)
#: NE: response.json() govdeyi JSON olarak cozer. Cozemezse ValueError firlatir
#:     (json.JSONDecodeError, ValueError'dan turer - yine 0.2).
#:
#:     Bu satirin STATUS KONTROLUNDEN ONCE gelmesi bu dosyanin en onemli karari:
#:     Last.fm gecersiz API key'e HTTP 200 doner ve hatayi govdeye koyar. Status'a
#:     once baksaydik en kritik hatayi HIC gormezdik.
#:
#:     Ama koşulsuz "cozulemedi = kalici hata" demek de yanlis olurdu: API'nin
#:     onundeki bir gateway 503 dondugunde govde HTML olur. O gecici bir arizadir.
#:     Bu yuzden decode hatasinda ONCE status'a bakiyoruz.
#:
#:     `response.text[:200]` - govdenin ilk 200 karakteri. Tamamini loglamak bir HTML
#:     sayfasini log'a bosaltmak demektir.
#:     `!r` - repr(). Ham str olsaydi HTML'deki satir sonlari log satirini bolerdi;
#:     repr her seyi tek satirda, \n gorunur halde tutar. Log satirinin tek satir
#:     kalmasi, grep edilebilirligin on kosuludur.
#:
#: KANIT:
#:   uv run python -c "
#:   s = 'satir1\nsatir2'
#:   print(f'ham: {s}')
#:   print(f'repr: {s!r}')     # tek satir
#:   "
        payload: dict[str, Any] = response.json()
    except ValueError as exc:
        # A gateway in front of the API answers 5xx with HTML, so the decode failure
        # alone would call a temporary outage permanent.
        if response.status_code in RETRYABLE_STATUS_CODES:
            raise LastfmTransientError(
                f"{method}: HTTP {response.status_code} with a non-JSON body"
            ) from exc
        raise LastfmError(
            f"{method}: HTTP {response.status_code} returned a non-JSON body: "
            f"{response.text[:200]!r}"
        ) from exc

    # Checked before the status, because an invalid API key arrives with status 200.
#: ----------------------------------------------------------------------------
#: ADIM 3/5 - HATA BELGESI
#: NE: `"error" in payload` sozlukte ANAHTAR arar (degerlerde degil). Gecersiz API
#:     key'i yakalayan satir budur - status kontrolu degil, cunku o cevap 200 ile
#:     gelir.
#:
#:     int(payload["error"]) neden bir try icinde: RETRYABLE_ERROR_CODES bir
#:     frozenset[int]. API bir gun "29" (string) dondurse, `"29" in {8,11,16,29}`
#:     SESSIZCE False olur - retry hic calismaz ve kimse fark etmez (0.6 tuzagi).
#:     int() donusumu bunu gurultuluye cevirir.
#:
#:     payload.get("message", "") - .get() anahtar yoksa patlamaz, varsayilani doner.
#:     payload["message"] olsaydi mesajsiz bir hata belgesi KeyError firlatirdi ve
#:     gercek hata (error 10) kaybolurdu.
#:
#:     Sonra taksonomi: kod kumede ise gecici (tenacity tekrar dener), degilse
#:     LastfmAPIError - kodu ve mesaji tasiyarak, ILK denemede yukari.
#:
#: KANIT (fixture ile, agsiz):
#:   uv run python -c "
#:   import json
#:   p = json.load(open('tests/fixtures/lastfm/error_3_invalid_method.json'))
#:   print('error' in p, p.get('message', ''), p.get('yok', 'VARSAYILAN'))
#:   "
    if "error" in payload:
        try:
            code = int(payload["error"])
        except (TypeError, ValueError) as exc:
            raise LastfmError(f"{method}: unreadable error document: {payload!r}") from exc
        message = str(payload.get("message", ""))
        if code in RETRYABLE_ERROR_CODES:
            raise LastfmTransientError(f"{method}: Last.fm error {code}: {message}")
        raise LastfmAPIError(code, message)

    # Backstop: valid JSON, no error document, but a status that still means failure.
#: ----------------------------------------------------------------------------
#: ADIM 4/5 - STATUS BACKSTOP  |  ADIM 5/5 - RETURN
#: NE: Buraya gelen cevap: gecerli JSON, icinde "error" yok, ama status hala kotu
#:     olabilir. Ornegin bir ara katmanin dondurdugu 500 + {} govdesi.
#:
#:     Nadir bir yol. Ama alternatifi bozuk bir payload'i "basari" diye dondurmek ve
#:     hatayi transform katmanina (P2.3) tasimak - orada teshis on kat zor olur.
#:
#:     KURAL: hatayi mumkun olan EN ERKEN katmanda yakala. Gec yakalanan hata,
#:     yanlis yerde patlar.
#:
#:     `return payload` - islenmemis, dokunulmamis payload. Bu modul veriyi
#:     RESHAPE ETMEZ: duzlestirme transform'un, saklama load'un isi. @attr (page,
#:     perPage, total) burada bozulursa rank kalici olarak kurtarilamaz hale gelir.
    if response.status_code in RETRYABLE_STATUS_CODES:
        raise LastfmTransientError(f"{method}: HTTP {response.status_code}")
    if response.status_code >= 400:
        raise LastfmError(
            f"{method}: HTTP {response.status_code} with no error document"
        )

    return payload


#: ----------------------------------------------------------------------------
#: NE: `_` ile baslayan ad, Python'da "bu modulun ic isi" demektir. Dil bunu ZORLAMAZ -
#:     disaridan cagrilabilir - ama sozlesme nettir: __init__.py'nin __all__ listesine
#:     girmez, degisirse kimseye haber verilmez. (docs/notes/22)
#:
#:     Bu fonksiyon SAYMAK icin var, DEGISTIRMEK icin degil. Payload'in icine bakar,
#:     track listesini dondurur, payload'a dokunmaz. Okumak yeniden sekillendirmek
#:     degildir - extract katmaninin "veriyi oldugu gibi dondur" sozlesmesi korunur.
#:
#:     isinstance(records, dict) kontrolu bir API tuhafligini kapatiyor: Last.fm'in
#:     JSON'u XML'den uretiliyor ve XML'de "tek elemanli liste" diye bir sey yoktur.
#:     Tek kayit kaldiginda liste sessizce nesneye coker. Bu kontrol olmasaydi len()
#:     cagrisi listenin uzunlugunu degil dict'in ANAHTAR SAYISINI sayardi - yanlis sayi,
#:     hata yok. Sessiz yanlis, gurultulu yanlistan pahalidir.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.extract.api import _track_records
#:   print(len(_track_records({'tracks': {'track': [{'a': 1}, {'b': 2}]}})))  # 2
#:   print(len(_track_records({'tracks': {'track': {'a': 1}}})))              # 1 <- sarildi
#:   print(len({'name': 'x', 'playcount': '9'}))                              # 2 <- sarilmasaydi
#:   "
#:
#: BIZDE: Dongunun govdesi 'kac kayit geldi' sorusunun NASIL cevaplandigiyla kirlenmiyor.
#:     XML kalintisi tek bir yerde yasiyor; yarin baska bir chart metodu eklenirse ayni
#:     yardimci kullanilir.
def _track_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the track list inside a chart payload, leaving the payload untouched.

    Reading is not reshaping: the caller needs a count, and the payload it stores must
    stay exactly as the API sent it.

    Raises:
        LastfmError: the payload did not carry a readable track list.
    """
    tracks = payload.get("tracks")
    if not isinstance(tracks, dict) or "track" not in tracks:
        raise LastfmError(
            f"{TOP_TRACKS_METHOD}: payload carried no track list: {payload!r}"
        )

    records = tracks["track"]
    # This JSON is generated from XML, so a one-element list arrives as a bare object.
    if isinstance(records, dict):
        return [records]
    if not isinstance(records, list):
        raise LastfmError(
            f"{TOP_TRACKS_METHOD}: unexpected track container: {type(records).__name__}"
        )
    return records


#: ============================================================================
#: NE: Bu modulun TEK PUBLIC fonksiyonu (_request alt cizgiyle basliyor: "ic kullanim,
#:     disaridan cagirma" - bu bir gelenek, Python engellemez).
#:
#:     Isim `get_...` degil `fetch_...`: fetch "aga cikiyorum, yavas olabilir, hata
#:     verebilir" cagrisimini tasir; get ucuz bir okuma gibi durur. Benim gorusum
#:     ama yaygin bir ayrim.
#:
#:     Imza:
#:       config: Config              - sir buradan gelir, os.environ'dan degil
#:       *, limit=100, page=1        - ayarlar, keyword-only (0.5)
#:       session: Session | None     - cagiran kendi session'ini verebilir
#:     Donen: dict[str, Any] - API'nin gonderdiginin AYNISI.
def fetch_top_tracks(
    config: Config,
    *,
    limit: int = 100,
    page: int = 1,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Return one page of ``chart.getTopTracks`` exactly as the API sent it.

    The payload is deliberately not reshaped: the raw layer stores this verbatim, and
    ``@attr`` (page, perPage, total) must survive because rank is derived from it.
    """
#: ----------------------------------------------------------------------------
#: NE: Sorgu parametreleri. requests bu sozlugu URL'e cevirir ve deger kacislarini
#:     (escaping) kendi yapar - string birlestirerek URL kurmak yerine hep bunu
#:     kullan.
#:
#:     "format": "json" OPSIYONEL DEGIL. Onsuz Last.fm XML doner, status yine 200
#:     olur, ve response.json() ValueError firlatir. Hatanin sebebi log'da "non-JSON
#:     body" olarak gorunur ama asil sebep unutulan tek bir parametredir.
#:
#:     str(limit) / str(page): requests int'i zaten cevirirdi. Acik cevirmenin sebebi
#:     istegin tel uzerindeki halinin cagiranin tipine BAGLI OLMAMASI - kayit,
#:     fixture ve log her zaman ayni gorunur.
#:
#:     api_key burada params'in icine giriyor ve params BIR DAHA ASLA loglanmiyor.
    params = {
        "method": TOP_TRACKS_METHOD,
        "api_key": config.lastfm_api_key,
        # Not optional: without it the API answers with XML and status 200.
        "format": "json",
        "limit": str(limit),
        "page": str(page),
    }

    # %s, not an f-string: logging skips formatting when the level is disabled. params is
    # never logged — it carries the API key.
#: ----------------------------------------------------------------------------
#: NE: Iki ayri kural tek satirda.
#:
#:     1. %s, f-string DEGIL. logging'e formatlanmis string degil, SABLON + ARGUMAN
#:        verirsin. Seviye kapaliysa (INFO kapali, sadece WARNING acik) logging
#:        formatlamayi HIC yapmaz. f-string ise cagri satirinda ANINDA formatlanir -
#:        loglanmayacak bir satir icin bile.
#:     2. params LOGLANMIYOR. Icinde api_key var. Bir sir bir kez log'a dustugunde,
#:        o log'un gittigi her yere (CloudWatch, S3, ucuncu parti) dusmus olur ve
#:        geri alinamaz.
#:
#:     INFO seviyesi neden: bu satir "sistem normal isini yapiyor" bilgisidir. DEBUG
#:     olsaydi prod'da gorunmezdi ve "pipeline calisti mi" sorusu cevapsiz kalirdi.
#:
#: KANIT (kapali seviyede formatlamanin hic olmadigini gosterir):
#:   uv run python -c "
#:   import logging; logging.basicConfig(level=logging.WARNING)
#:   class Patlar:
#:       def __str__(self): raise RuntimeError('formatlandim!')
#:   logging.getLogger('x').info('deger=%s', Patlar())   # sessiz - hic formatlanmadi
#:   print('formatlama hic calismadi')
#:   "
    logger.info("fetching %s page=%s limit=%s", TOP_TRACKS_METHOD, page, limit)

#: ----------------------------------------------------------------------------
#: NE: `session or requests.Session()` - Python'da `or` bool dondurmez, IKI OPERANDDAN
#:     BIRINI dondurur: soldaki "truthy" ise onu, degilse sagdakini. None falsy
#:     oldugu icin bu "verilmisse onu kullan, verilmemisse yenisini yap" demektir.
#:
#:     Neden varsayilan deger olarak `session: Session = requests.Session()` YAZMADIK:
#:     Python varsayilan degerleri fonksiyon TANIMLANIRKEN bir kez hesaplar, her
#:     cagrida degil. Boyle yazsaydik butun program omru boyunca TEK bir session
#:     paylasilirdi - klasik "mutable default argument" tuzagi.
#:
#: KANIT:
#:   uv run python -c "
#:   def kotu(x=[]):
#:       x.append(1); return x
#:   print(kotu(), kotu(), kotu())    # [1] [1,1] [1,1,1]  <- ayni liste!
#:   print(None or 'yedek', 'asil' or 'yedek')
#:   "
#:
#: BIZDE: P2.1'in sayfalama ihtiyaci (ADR-0006: hedef sayiya kadar sayfala) bu
#:     fonksiyonu ust uste cagiracak. O cagiran kendi Session'ini verirse TCP+TLS el
#:     sikismasi sayfa basina tekrarlanmaz.
    return _request(session or requests.Session(), TOP_TRACKS_METHOD, params)


#: ============================================================================
#: BOLUM 5 - SAYFALAMA: DONGU NEREDE DURUR, NE DONDURUR
#: ============================================================================
#: NE: Bu fonksiyonun tek zor karari sudur: dongu ne zaman duracak? Dort aday vardi.
#:
#:       1. ceil(target / page_size) kadar sayfa cek       -> YANLIS
#:       2. @attr icindeki totalPages'e kadar cek          -> YANLIS
#:       3. Biriken GERCEK kayit sayisi >= target          -> dogru, tek basina yetmez
#:       4. Gelen sayfa bos -> dur                         -> 3'un sonsuz dongu korumasi
#:
#:     1 neden yanlis: aritmetik, page_size'in UYGULANDIGINI varsayar. Last.fm `limit`i
#:     kirparsa cevap sessizce kisa gelir - HTTP 200, hata belgesi yok. 100 istedin, 40
#:     geldi; ceil(100/100)=1 dedigi icin dongu biter ve 40 kayit "tam" sayilir. Uc ay
#:     kimse fark etmez, edildiginde chart geriye donuk cekilemedigi icin veri geri
#:     gelmez. ADR-0006 tam bunu onlemek icin yazilmisti; ADR-0015 nereye koyacagimizi.
#:
#:     2 neden yanlis: totalPages = total / perPage ve `total` sabit 10000 - gercek bir
#:     sayim degil, tavan (1.8'de olculdu). Yani totalPages hicbir zaman "bitti" demez.
#:
#:     Donus tipi list[dict], generator degil: yield edilseydi hata 3. sayfada ciktiginda
#:     cagiran ilk iki sayfayi coktan S3'e yazmis olurdu. list ile ya hepsi ya hicbiri.
#:     Esik: sonuc bellege sigmadigi gun generator dogru cevap olur. (docs/notes/24)
#:
#:     Sayfalar BIRLESTIRILMEDEN donuyor. Birlestirme her sayfanin @attr'ini (page,
#:     perPage) silerdi ve rank bu ikisinden turuyor - kurtarilamaz kayip.
#:
#: KANIT: (dongu sunucunun sozune degil kendi saydigina bakiyor + tavan calisiyor)
#:   uv run python -c "
#:   import logging; logging.basicConfig(level=logging.INFO)
#:   from lastfm_etl.config import load_config
#:   from lastfm_etl.extract import fetch_top_tracks_pages
#:   print(len(fetch_top_tracks_pages(load_config())))                       # 2
#:   print(len(fetch_top_tracks_pages(load_config(), page_size=100)))        # 1
#:   print(len(fetch_top_tracks_pages(load_config(), target=10**6, max_pages=3)))
#:   "                                                                       # 3 + WARNING
#:
#: ----------------------------------------------------------------------------
#: NE: `session = session or requests.Session()` satiri DONGUNUN DISINDA.
#:     `a or b` Python'da bool dondurmez: a "dogru" ise a'yi, degilse b'yi dondurur.
#:     Burada "cagiran session verdiyse onu kullan, vermediyse bir tane uret" demek.
#:
#:     Dongunun ICINDE olsaydi her sayfa yeni bir Session, yani yeni TCP el sikismasi
#:     olurdu. Session'in tek varlik sebebi baglanti havuzu (connection pool): ayni
#:     baglantiyi tekrar kullanmak. Her cagrida yenisini acmak, Session kullanmamakla
#:     ayni sey - ustelik daha yaniltici, cunku kod dogru gorunur.
#:
#: KANIT:
#:   uv run python -c "
#:   print(None or 'uretildi')     # uretildi
#:   print('verildi' or 'uretildi') # verildi
#:   "
#:
#: BIZDE: fetch_top_tracks'in kendi `session or requests.Session()` satiri duruyor, ama
#:     buradan session GECILDIGI icin orada yeni nesne uretilmiyor. Iki sayfa, tek
#:     baglanti.
#:
#: ----------------------------------------------------------------------------
#: NE: `for ... else:` - Python'un en cok yanlis okunan yapisi. `else`, dongu bittiginde
#:     DEGIL, dongu HIC `break` GORMEDEN bittiginde calisir. Adi talihsiz; "nobreak"
#:     olsaydi kimse yanlis okumazdi.
#:
#:     Burada tam olarak "tavana carptim ve hedefe ulasamadim" demenin tek adimli yolu.
#:     Alternatifi `hit_ceiling = True` gibi bir bayrak degiskeni tutmaktir: ayni is,
#:     fazladan durum, ve guncellenmeyi unutulabilecek fazladan bir satir.
#:
#: KANIT:
#:   uv run python -c "
#:   for i in range(3):
#:       if i == 5: break
#:   else:
#:       print('break gormedi -> else calisti')
#:   for i in range(3):
#:       if i == 1: break
#:   else:
#:       print('bu satir hic basilmaz')
#:   "
#:
#: BIZDE: Iki `break` de normal cikis (hedefe ulasildi / kaynak tukendi) - bunlarda
#:     WARNING basilmaz. Yalnizca hicbiri calismadan `range` tukenirse tavan baglamistir
#:     ve o zaman log'a dusen bir WARNING kalir. Exception firlatilmiyor: karar ve
#:     gerekcesi ADR-0015'in son maddesinde, bilincli bir asimetri.
def fetch_top_tracks_pages(
    config: Config,
    *,
    target: int = TARGET_TRACK_COUNT,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int = MAX_PAGES,
    session: requests.Session | None = None,
) -> list[dict[str, Any]]:
    """Return whole page payloads until ``target`` tracks have been seen.

    Pages come back verbatim and unmerged: rank is derived from ``@attr`` (page,
    perPage) plus a record's position inside its page, so merging would destroy it.

    The loop stops on the number of records actually received, never on arithmetic over
    ``page_size``. Last.fm may answer with fewer records than requested and reports no
    error when it does, so a computed page count would end the run short and silently.

    Returns:
        One element per page, in request order. The total may exceed ``target``;
        trimming belongs to the transform layer, which is allowed to reshape.

    Raises:
        LastfmError: a page carried no readable track list.
        LastfmAPIError: the API returned a permanent error document.
        LastfmTransientError: a retryable failure outlived every attempt.
    """
    # One session for every page: the connection pool only pays off when the same
    # object is reused, and fetch_top_tracks would otherwise open a fresh one per call.
    session = session or requests.Session()

    pages: list[dict[str, Any]] = []
    collected = 0

    for page in range(1, max_pages + 1):
        payload = fetch_top_tracks(config, limit=page_size, page=page, session=session)
        records = _track_records(payload)

        if not records:
            logger.info("page %s carried no tracks, stopping early", page)
            break

        pages.append(payload)
        collected += len(records)

        if collected >= target:
            break
    else:
        # Reached only when no break ran: the ceiling bound before the target was met.
        logger.warning(
            "stopped at the %s page ceiling with %s of %s tracks",
            max_pages,
            collected,
            target,
        )

    logger.info("collected %s tracks across %s pages", collected, len(pages))
    return pages

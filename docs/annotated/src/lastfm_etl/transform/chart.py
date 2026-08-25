#: ============================================================================
#: YORUMLU AYNA - src/lastfm_etl/transform/chart.py
#: ============================================================================
#: "#:" ile baslayan her satir aciklamadir ve gercek dosyada YOKTUR.
#: Kalan her karakter src/lastfm_etl/transform/chart.py ile birebir aynidir. Sapma kontrolu:
#:   grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/transform/chart.py | diff - src/lastfm_etl/transform/chart.py
#: Cikti bossa ayna guncel.
#:
#: Yazim sozlesmesi (docs/annotated/README.md):
#:   NE    - bu sozdizimi/nesne aslinda nedir, Python bununla ne yapar
#:   KANIT - iddiayi calistirarak dogrulayan komut
#:   BIZDE - bizim kodda tam olarak neyi degistiriyor
#:
#: Bu dosyayi OKUMAK yetmez. KANIT komutlarini terminalde calistir.
#:
#: Veri sozlesmesi: docs/SCHEMA.md - mimari karar: docs/adr/0016
#: Sayfalama ve @attr: docs/adr/0015, docs/notes/23
#:
#: ============================================================================
#: BOLUM 0 - ONCE SU YEDI KAVRAM
#: ============================================================================
#: Hicbiri bu dosyaya ozel degil. Bilinmeden asagisi okunmaz.
#:
#: ----------------------------------------------------------------------------
#: 0.1 - .get() ZINCIRI, VE NEDEN [] DEGIL
#: ----------------------------------------------------------------------------
#: NE: d["x"] anahtar yoksa KeyError firlatir. d.get("x") None dondurur, patlamaz.
#:     Ikisi de dogru; sorun HANGISININ NE ZAMAN dogru oldugu.
#:
#:     Kural: anahtarin VAR OLMASI bizim garantimizse [] kullan - yoksa bu bir bug'dir
#:     ve gurultulu patlamalidir. Anahtar DIS DUNYADAN geliyorsa .get() kullan ve
#:     yoklugu bir veri durumu olarak ele al.
#:
#:     Last.fm payload'i dis dunyadir. Olculdu: `mbid` anahtari 19 kayittan 4'unde
#:     HIC YOK. record["mbid"] yazan kod, 5. kayitta KeyError ile olur.
#:
#: KANIT:
#:   uv run python -c "
#:   d = {'a': 1}
#:   print(d.get('yok'))          # None
#:   print(d.get('yok', 'varsayilan'))
#:   try: d['yok']
#:   except KeyError as e: print('KeyError:', e)
#:   "
#:
#: BIZDE: Payload'dan okunan HER alan .get() ile okunuyor. Tek istisna _rank icindeki
#:     attr["page"] - orada yoklugu sessizce gecmek istemiyoruz, bilerek patlatiyoruz.
#:
#: ----------------------------------------------------------------------------
#: 0.2 - isinstance, VE NEDEN type(x) == y DEGIL
#: ----------------------------------------------------------------------------
#: NE: isinstance(x, dict) "x bir dict mi ya da dict'ten tureyen bir sey mi" diye
#:     sorar. type(x) == dict ise kalitimi reddeder. JSON'dan gelen veride ikisi ayni
#:     sonucu verir, ama isinstance yaygin ve dogru refleks olandir.
#:
#:     Asil onemli olan: isinstance bir TIP KAPISIDIR. json.load() sana dict, list,
#:     str, int, float, bool veya None dondurur - hangisi oldugunu SEN bilmezsin,
#:     sunucu bilir. Tip varsayimi yapan her satir, sunucunun bir gun fikrini
#:     degistirmesiyle TypeError'a doner.
#:
#: KANIT:
#:   uv run python -c "
#:   print(isinstance(True, int))     # True  <- bool int'ten turer, saskin edici
#:   print(type(True) == int)         # False
#:   print(isinstance({}, dict), isinstance([], dict))
#:   "
#:
#: BIZDE: _text, _records ve dongu govdesi tip kapisiyla basliyor. Amac savunma degil,
#:     KARAR: beklenmeyen tip gelirse satiri mi atacagiz, kosuyu mu durduracagiz.
#:
#: ----------------------------------------------------------------------------
#: 0.3 - enumerate VE "SAYFA ICI INDEX"
#: ----------------------------------------------------------------------------
#: NE: enumerate(liste) her turda (index, eleman) ciftini uretir. index her CAGRIDA
#:     sifirdan baslar - yani ic ice iki dongude, ic dongunun index'i her dis turda
#:     sifirlanir.
#:
#:     Bu bir hata degil, tam olarak istedigimiz sey. rank'i global bir sayacla
#:     uretseydik dogru gorunurdu ve YANLIS olurdu: olculdu, son sayfa 20 degil 19
#:     kayit dondu. Global sayac o noktadan sonra bir kayardi ve hicbir yerde hata
#:     gorunmezdi.
#:
#: KANIT:
#:   uv run python -c "
#:   sayfalar = [['a','b'], ['c']]
#:   for s in sayfalar:
#:       for i, x in enumerate(s): print(i, x)   # 0 a / 1 b / 0 c  <- sifirlaniyor
#:   "
#:
#: BIZDE: index sayfa icidir; sayfa numarasi @attr'dan gelir. rank ikisinin
#:     birlesimidir - docs/SCHEMA.md, kolon 2.
#:
#: ----------------------------------------------------------------------------
#: 0.4 - set VE TUPLE ANAHTAR (hashable ne demek)
#: ----------------------------------------------------------------------------
#: NE: set, "icinde var mi" sorusunu eleman sayisindan BAGIMSIZ surede cevaplayan bir
#:     koleksiyondur. Liste ile ayni soru her seferinde bastan tarama demektir.
#:
#:     set'e (ve dict anahtarina) yalnizca HASHABLE nesne konur: degismeyen nesne.
#:     tuple hashable, list degil. ("a","b") anahtar olabilir, ["a","b"] olamaz -
#:     cunku listeyi sonradan degistirirsen hash'i degisir ve nesne kendi kovasinda
#:     kaybolur.
#:
#: KANIT:
#:   uv run python -c "
#:   s = {('a','b')}
#:   print(('a','b') in s, ('a','c') in s)
#:   try: {['a','b']}
#:   except TypeError as e: print('TypeError:', e)
#:   "
#:
#: BIZDE: seen bir set[tuple[str, str]]. Bilesik anahtarimiz (artist_name, track_name)
#:     ve tekrar kontrolu bununla yapiliyor. 100 satirda liste de yeterdi; kalibin
#:     dogru olmasi 100 milyon satirda ayni kodu yazabilmek demek.
#:
#: ----------------------------------------------------------------------------
#: 0.5 - dict.setdefault
#: ----------------------------------------------------------------------------
#: NE: d.setdefault(k, v) - k varsa mevcut degeri dondurur ve HICBIR SEY DEGISTIRMEZ;
#:     yoksa v'yi yazar ve v'yi dondurur. Yani "ilk goren kazanir" davranisi.
#:
#:     Bilinmesi gereken tuzak: v ifadesi, yazilmayacak olsa bile HER CAGRIDA
#:     hesaplanir. Pahali bir ifade koyarsan her turda bosuna calisir.
#:
#: KANIT:
#:   uv run python -c "
#:   def pahali():
#:       print('  hesaplandi'); return 2
#:   d = {}
#:   d.setdefault('a', pahali()); d.setdefault('a', pahali())
#:   print(d)   # {'a': 2} - ikinci pahali() de CALISTI ama yazilmadi
#:   "
#:
#: BIZDE: artists sozlugu. Bir sanatci chart'ta 12 kez gorunuyor olabilir (olculdu:
#:     20 parcada 6 sanatci); ilk gorulen satir tutuluyor. Sayfalar sirali oldugu icin
#:     "ilk gorulen" = "en iyi rank'a sahip olan".
#:
#: ----------------------------------------------------------------------------
#: 0.6 - `a or b` ILE VARSAYILAN DEGER, VE TUZAGI
#: ----------------------------------------------------------------------------
#: NE: `a or b` bool dondurmez: a "truthy" ise a'yi, degilse b'yi dondurur.
#:     Falsy olanlar: None, False, 0, 0.0, "", [], {}, set().
#:
#:     TUZAK: "deger verilmediyse varsayilani kullan" ile "deger falsy ise varsayilani
#:     kullan" AYNI SEY DEGIL. Sayisal bir parametrede `x = x or 10` yazarsan,
#:     cagiran x=0 verdiginde sessizce 10 olur.
#:
#: KANIT:
#:   uv run python -c "
#:   def f(x=None): return x or 10
#:   print(f(), f(5), f(0))    # 10 5 10  <- sonuncusu BUG olurdu
#:   "
#:
#: BIZDE: `snapshot_date or datetime.now(UTC).date()` guvenli, cunku bir date nesnesi
#:     asla falsy degildir. Ayni satiri bir int parametresi icin yazsaydik bug olurdu.
#:     Kural: `or` varsayilani yalnizca falsy olamayacak tiplerde kullan.
#:
#: ----------------------------------------------------------------------------
#: 0.7 - AWARE vs NAIVE datetime
#: ----------------------------------------------------------------------------
#: NE: datetime iki cesittir. NAIVE olanin tzinfo'su None'dur - hangi saat diliminde
#:     oldugu YAZMAZ. AWARE olan saat dilimini tasir.
#:
#:     datetime.now() naive ve YEREL saat dondurur. Ayni kod senin makinende UTC+3,
#:     Lambda'da UTC uretir - ayni ani gosteren iki farkli sayi, ve hicbiri hangisi
#:     oldugunu soylemez. Dogrusu: datetime.now(UTC).
#:
#:     isoformat() aware bir datetime'da "+00:00" eki basar. ISO 8601 "Z" ile "+00:00"
#:     ayni seydir; "Z" daha yaygin ve Athena/Glue tarafinda daha az surprizlidir.
#:
#: KANIT:
#:   uv run python -c "
#:   from datetime import datetime, UTC
#:   n = datetime.now(); a = datetime.now(UTC)
#:   print(n.tzinfo, a.tzinfo)
#:   print(n.isoformat()); print(a.isoformat())
#:   "
#:
#: BIZDE: naive bir ingested_at TransformError ile REDDEDILIYOR. Kabul edilseydi UTC
#:     gibi yazilirdi ve hicbir okuyucu yanlis oldugunu anlayamazdi - sessiz veri
#:     bozulmasinin ders kitabi ornegi.
#:
#: ============================================================================
"""Turn Last.fm chart payloads into the rows of the two curated tables.

The contract this module implements — columns, types, keys and the policy for unusable
rows — is `docs/SCHEMA.md`. When the two disagree, the document is the specification and
this file is the bug.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Final

logger = logging.getLogger(__name__)

#: ----------------------------------------------------------------------------
#: NE: Sabitin adi bir KARAR tasiyor. `if duration == 0` yazan kod, okuyana "sifir
#:     saniyelik parca" dedirtir. UNKNOWN_DURATION adi, 0'in bir OLCUM degil bir
#:     YOKLUK BILDIRIMI oldugunu soyler. Ayni sayi, iki farkli anlam - ve fark yalnizca
#:     isimde yasiyor.
#:
#: BIZDE: docs/SCHEMA.md kolon 7: duration_seconds nullable ve "0 -> null". Bu satir o
#:     kuralin koddaki karsiligi.
# Last.fm sends "0" for a duration it does not know, not for a zero-length track.
UNKNOWN_DURATION: Final = 0


#: ----------------------------------------------------------------------------
#: NE: Tek bir exception tipi var - extract'ta uc tane vardi. Sebep: orada cagiranin
#:     vermesi gereken bir KARAR vardi (tekrar dene / deneme / hata belgesini oku).
#:     Burada oyle bir karar yok: dogru payload ya vardir ya yoktur, retry bir sey
#:     duzeltmez.
#:
#:     Ders: exception hiyerarsisinin derinligi, cagiranin verecegi karar sayisi kadar
#:     olmalidir. Kullanilmayan her ayrim, bakimi olan olu koddur.
#:
#: BIZDE: Bozuk SAYFA -> TransformError (kosu durur). Bozuk SATIR -> WARNING + atilir
#:     (kosu devam eder). Bu ayrim bu dosyanin en onemli tasarim karari.
class TransformError(Exception):
    """Raised when a payload cannot be read at all, unlike a single unusable row."""


#: ----------------------------------------------------------------------------
#: NE: dataclass ayrintili anlatimi config.py aynasinda (Bolum 0.2). Burada yalnizca
#:     yeni olan: frozen=True nesnenin KENDI alanlarinin yeniden atanmasini engeller,
#:     ama alanin ICINDEKI listeyi dondurmaz.
#:
#:     Yani tables.tracks = [] hata verir; tables.tracks.append(...) CALISIR. Buna
#:     "sig immutability" (shallow) denir. Python'da derin dondurma yoktur.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.transform import ChartTables
#:   t = ChartTables(tracks=[], artists=[])
#:   t.tracks.append(1); print(t.tracks)          # calisti
#:   try: t.tracks = []
#:   except Exception as e: print(type(e).__name__, e)
#:   "
#:
#: BIZDE: Amac koruma degil, ISIMLENDIRME. Fonksiyon iki liste donduruyor ve
#:     `tracks, artists = f()` sirasi karistirilabilir bir seydir - tip ipucu da
#:     yakalamaz, ikisi de list[dict]. tables.tracks yaziminda karistiracak bir sey yok.
@dataclass(frozen=True, slots=True)
class ChartTables:
    """The two curated tables produced by one run, in chart order.

    A pair of named lists rather than a tuple: at the call site `tables.tracks` says
    what it holds and `tables[0]` does not.
    """

    tracks: list[dict[str, Any]]
    artists: list[dict[str, Any]]


#: ----------------------------------------------------------------------------
#: NE: Uc satirlik bu fonksiyon bir POLITIKA. "Yok" kavraminin bu veri kaynagindaki
#:     uc kiligi - anahtar yok / bos string / sadece bosluk - tek bir None'a
#:     indirgeniyor. Politika tek yerde durunca, degistigi gun tek yerde degisir.
#:
#:     `return stripped or None` satiri 0.6'daki kalip: bos string falsy oldugu icin
#:     None doner. Burada guvenli, cunku donen tip zaten str | None.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.transform.chart import _text
#:   print(_text('  a  '), _text(''), _text('   '), _text(None), _text(5))
#:   "                                    # a None None None None
#:
#: BIZDE: Dokuz alanin tamami bundan geciyor. record.get('mbid') bos string dondugunde
#:     de, anahtar hic olmadiginda da sonuc ayni: None. docs/SCHEMA.md'nin "null" sutunu
#:     tam olarak bu fonksiyonun cikti kumesi.
def _text(value: Any) -> str | None:
    """Return a stripped, non-empty string, or None.

    This payload expresses "absent" three ways in the same field: a missing key, an
    empty string, and whitespace. Collapsing them here stops every caller from
    repeating it.
    """
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


#: ----------------------------------------------------------------------------
#: NE: try'in NEYI SARDIGINA bak: yalnizca int(text). _text cagrisi disarida, cunku o
#:     zaten patlamaz. try blogu ne kadar genisse, yakaladigin hatanin nereden geldigi
#:     o kadar belirsizdir - ve bir gun beklemedigin bir hata da ayni excep'e duser.
#:
#:     TypeError yakalanmiyor, cunku _text zaten str olmayani None yapti; buraya str
#:     disi bir sey ULASAMAZ. Yakalanmayan bir hata tipi, "bu durum imkansiz"
#:     iddiasidir - ve o iddia yanlissa gurultulu patlamasini istiyoruz.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.transform.chart import _to_int
#:   print(_to_int('42'), _to_int(' 42 '), _to_int('yok'), _to_int(''), _to_int(None))
#:   print(_to_int('4.2'))     # None <- int('4.2') ValueError verir, float degil
#:   "
#:
#: BIZDE: playcount/listeners None donerse satir ATILIR (not-null kolonlar), duration
#:     None donerse satir KALIR (nullable kolon). Ayni fonksiyon, iki farkli sonuc -
#:     karari veren fonksiyon degil, cagiran.
def _to_int(value: Any) -> int | None:
    """Return the value as an int, or None when it is absent or not a number.

    Every numeric field in this payload arrives as a string, so this is not defensive
    coding — it is the actual type boundary of the pipeline.
    """
    text = _text(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


#: ----------------------------------------------------------------------------
#: NE: Bu projenin en kritik dort satiri. rank payload'da HICBIR ALANDA yok ve hicbir
#:     alandan turetilemiyor - 1.7'de olculdu: 500. sayfadaki bir parcanin playcount'u
#:     1. sayfadakinden 7 kat buyuk olabiliyor. Yani ROW_NUMBER() OVER (ORDER BY
#:     playcount DESC) ile sorgu aninda uretmek ELENDI. rank materyalize edilmek zorunda.
#:
#:     attr["page"] ve attr["perPage"] .get() ILE DEGIL koseli parantezle okunuyor -
#:     0.1'deki kuralin ikinci yarisi. Burada yokluk bir veri durumu degil, bir
#:     felakettir: rank uretilemezse o sayfanin tamami anlamsizdir.
#:
#:     Uc hata tipi birlikte yakalaniyor: KeyError (anahtar yok), TypeError (attr None
#:     ya da liste), ValueError (int('x')). Ucu de ayni sonuca varir, ucu de ayni
#:     mesaji hak eder.
#:
#:     `from exc` zinciri korur: traceback'te hem bizim mesajimiz hem asil hata gorunur.
#:
#: KANIT:
#:   uv run python -c "
#:   from lastfm_etl.transform.chart import _rank
#:   print(_rank({'page':'1','perPage':'50'}, 0))    # 1
#:   print(_rank({'page':'2','perPage':'50'}, 0))    # 51   <- sayfa siniri
#:   print(_rank({'page':'500','perPage':'20'}, 0))  # 9981 <- fixture ile dogrulandi
#:   try: _rank({'page':'x','perPage':'20'}, 0)
#:   except Exception as e: print(type(e).__name__, '|', e.__cause__.__class__.__name__)
#:   "
#:
#: BIZDE: perPage bizim DEFAULT_PAGE_SIZE sabitimizden DEGIL, sunucunun cevabindan
#:     okunuyor. Sabit yazilsaydi, config degisip @attr degismedigi gun (ya da tersi)
#:     rank sessizce kayardi ve bunu fark etmenin hicbir yolu olmazdi.
def _rank(attr: dict[str, Any], index: int) -> int:
    """Return the chart position of the record at `index` within its page.

    Both numbers come from the response's own `@attr`, never from the page size we asked
    for: the server decides what a page holds, and one short page in the middle would
    otherwise shift every rank after it.

    Raises:
        TransformError: the page carried no readable @attr.
    """
    try:
        page = int(attr["page"])
        per_page = int(attr["perPage"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TransformError(
            f"rank cannot be derived from this @attr: {attr!r}"
        ) from exc
    return (page - 1) * per_page + index + 1


#: ----------------------------------------------------------------------------
#: NE: Donus tipi bir tuple: (attr, records). Iki deger donduren fonksiyonlarda tuple
#:     yaygin ve kabul edilebilir - ChartTables gibi bir sinifa gerek yok, cunku bu
#:     fonksiyon modul ici (_ ile basliyor) ve tek bir yerden cagriliyor. Sinif acmak
#:     da yanlis olmazdi; olcut "kac cagrim var ve karistirilabilir mi".
#:
#:     isinstance(records, dict) kontrolu extract/api.py'deki _track_records ile AYNI
#:     tuhafligi kapatiyor: Last.fm JSON'u XML'den uretiliyor ve XML'de "tek elemanli
#:     liste" diye bir sey yok, tek kayit kaldiginda liste nesneye coker.
#:
#:     Ayni kontrolun iki dosyada olmasi bilincli bir TEKRAR. Ortak bir yardimciya
#:     cikarilabilirdi, ama o yardimci hangi katmana ait olurdu? extract'a koysak
#:     transform extract'i import ederdi ve tek yonlu bagimlilik kirilirdi. Iki satir
#:     tekrar, bir katman ihlalinden ucuzdur.
#:
#: BIZDE: Bu fonksiyondan cikan her TransformError kosuyu durdurur. Satir atmakla sayfa
#:     reddetmek arasindaki sinir tam olarak burasi.
def _records(page: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    """Return one page's @attr and its track list.

    Raises:
        TransformError: the page is not a chart payload. A page that cannot be read is
            not a bad row — every rank behind it would be wrong, so the run stops.
    """
    container = page.get("tracks")
    if not isinstance(container, dict):
        raise TransformError(f"payload carried no track container: {page!r}")

    attr = container.get("@attr")
    if not isinstance(attr, dict):
        raise TransformError(f"page carried no @attr: {container.keys()}")

    records = container.get("track")
    # Generated from XML, where a one-element list is indistinguishable from an object.
    if isinstance(records, dict):
        return attr, [records]
    if not isinstance(records, list):
        raise TransformError(f"unexpected track container: {type(records).__name__}")
    return attr, records


#: ============================================================================
#: BOLUM 1 - ASIL DONUSUM
#: ============================================================================
#: NE: Imzada iki sey dikkat cekmeli.
#:
#:     (1) snapshot_date ve ingested_at PARAMETRE, fonksiyon icinde now() cagrisi degil.
#:     Sebep tek kelimeyle: TESTLENEBILIRLIK. Ici now() cagiran bir fonksiyonun ciktisi
#:     her calistirmada farklidir; ona karsi assert yazamazsin. Bu kalibin adi
#:     "dependency injection" - bagimliligi (burada: saat) disaridan vermek.
#:
#:     (2) `*` ile keyword-only. transform_chart(pages, d1, d2) yazilamaz; hangi
#:     tarihin hangisi oldugu cagri yerinde OKUNUR olmak zorunda. Iki ayni tipli
#:     parametre yan yanaysa keyword-only neredeyse her zaman dogrudur.
#:
#: KANIT: (ayni girdi -> ayni cikti, saatten bagimsiz)
#:   uv run python -c "
#:   import json
#:   from datetime import date, datetime, UTC
#:   from lastfm_etl.transform import transform_chart
#:   p = json.load(open('tests/fixtures/lastfm/chart_gettoptracks_success.json'))
#:   D = dict(snapshot_date=date(2026,8,25), ingested_at=datetime(2026,8,25,3,0,tzinfo=UTC))
#:   a = json.dumps(transform_chart([p], **D).tracks)
#:   b = json.dumps(transform_chart([p], **D).tracks)
#:   print('deterministik:', a == b)
#:   "
def transform_chart(
    pages: list[dict[str, Any]],
    *,
    snapshot_date: date | None = None,
    ingested_at: datetime | None = None,
) -> ChartTables:
    """Turn one run's page payloads into the rows of both curated tables.

    Both tables come out of a single pass, so every `tracks.artist_name` exists in
    `artists` by construction rather than by discipline. Parsing the same payload twice
    is how a foreign key silently starts pointing at nothing.

    Rows whose key components are unusable are dropped and counted, not repaired: a row
    with a null key survives every later check, and a missing row does not. The policy
    per field is in `docs/SCHEMA.md`.

    Both timestamps are parameters rather than calls to now(), so one run can produce
    the same output twice and a test never depends on the clock.

    Raises:
        TransformError: a page carried no readable track list or no readable @attr, or
            ingested_at was naive.
    """
#:     ----------------------------------------------------------------------
#: NE: Parametrenin uzerine YAZILIYOR (snapshot_date = snapshot_date or ...). Bu
#:     Python'da yaygin ve kabul gormus bir kalip; alternatifi ikinci bir isim
#:     uretmektir (resolved_snapshot_date gibi) ve o isim hicbir sey kazandirmaz.
#:
#:     Varsayilan degerin imzada degil GOVDEDE hesaplanmasinin sebebi: imzadaki
#:     varsayilan deger fonksiyon TANIMLANDIGINDA bir kez hesaplanir. def f(t=now())
#:     yazsaydik, t modulun import edildigi ana donardi ve Lambda'nin sicak
#:     invocation'larinda gunlerce ayni tarih yazilirdi. Bu, Python'un en meshur
#:     tuzagi (mutable/dinamik default argument).
#:
#: KANIT:
#:   uv run python -c "
#:   import time
#:   def kotu(t=time.time()): return t
#:   print(kotu()); time.sleep(1); print(kotu())   # AYNI sayi - donmus
#:   "
#:
#: BIZDE: naive datetime reddi de burada. docs/SCHEMA.md ingested_at'i UTC olarak
#:     tanimliyor; naive bir deger o sozlesmeyi sessizce yalanlardi.
    snapshot_date = snapshot_date or datetime.now(UTC).date()
    ingested_at = ingested_at or datetime.now(UTC)
    if ingested_at.tzinfo is None:
        raise TransformError(
            "ingested_at must be timezone-aware; a naive value would be written as if "
            "it were UTC and no reader could tell"
        )

    # Serialised once, not per row: JSON has no date type, so both leave as strings.
    snapshot = snapshot_date.isoformat()
    ingested = ingested_at.astimezone(UTC).isoformat().replace("+00:00", "Z")

#:     ----------------------------------------------------------------------
#: NE: Dort birikimci degisken, dongunun DISINDA. Tip ipuclari bos koleksiyonlarda
#:     zorunlu sayilir: mypy `tracks = []` satirindan iceriginin ne oldugunu bilemez,
#:     `list[dict[str, Any]]` yazmadikca sonraki her append kontrol edilmez.
#:
#:     artists neden dict, list degil? Cunku "bu sanatci daha once gorulduyse atla"
#:     sorusunu cevaplamasi gerekiyor. Liste olsaydi her turda bastan aranirdi.
#:     dict'in anahtari zaten tekillik demek.
#:
#:     Python 3.7'den beri dict EKLEME SIRASINI korur - yani list(artists.values())
#:     sanatcilari ilk gorulme sirasiyla, yani rank sirasiyla dondurur. Bu bir
#:     uygulama detayi degil, dilin garantisi.
#:
#: KANIT:
#:   uv run python -c "
#:   d = {}; d['z']=1; d['a']=2; d['m']=3
#:   print(list(d))    # ['z','a','m'] - alfabetik degil, EKLEME sirasi
#:   "
    tracks: list[dict[str, Any]] = []
    artists: dict[str, dict[str, Any]] = {}
    seen: set[tuple[str, str]] = set()
    dropped = 0

#:     ----------------------------------------------------------------------
#: NE: Ic ice iki dongu, ama tek bir GECIS. Payload bir kez ayristiriliyor ve iki tablo
#:     ayni turda uretiliyor.
#:
#:     Kursun kodu bunu UC ayri fonksiyonla yapiyordu (album(), artist(), song()) ve her
#:     biri payload'i bastan geziyordu. Sonucu gercek bir bug: song()'un artist_id'si
#:     row['track']['album']['artists'][0] yolundan, artist() ise
#:     row['track']['artists'] yolundan geliyordu. Iki farkli yol, iki farkli sonuc -
#:     ve bir sarkinin FK'si artist tablosunda OLMAYAN bir id'ye isaret edebiliyordu.
#:     JOIN sessizce satir kaybettirir; hicbir yerde hata gorunmez.
#:
#:     Tek gecis bu hatayi imkansiz kilar. "Dikkatli yazariz" ile "yazilamaz" arasindaki
#:     fark, ADR-0012'nin iki bucket gerekcesiyle ayni dusunce.
#:
#: KANIT: (her tracks.artist_name artists'te var mi)
#:   uv run python -c "
#:   import json
#:   from lastfm_etl.transform import transform_chart
#:   p = json.load(open('tests/fixtures/lastfm/chart_gettoptracks_success.json'))
#:   t = transform_chart([p])
#:   names = {a['artist_name'] for a in t.artists}
#:   print(all(x['artist_name'] in names for x in t.tracks))   # True
#:   "
    for page in pages:
        attr, records = _records(page)

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                dropped += 1
                logger.warning("dropped a non-object row at index %s", index)
                continue

            artist = record.get("artist")
            artist = artist if isinstance(artist, dict) else {}
            artist_name = _text(artist.get("name"))
            track_name = _text(record.get("name"))
            if artist_name is None or track_name is None:
                dropped += 1
                logger.warning(
                    "dropped a row with no usable key: artist=%r track=%r",
                    artist_name,
                    track_name,
                )
                continue

            playcount = _to_int(record.get("playcount"))
            listeners = _to_int(record.get("listeners"))
            if playcount is None or listeners is None:
                dropped += 1
                logger.warning(
                    "dropped %r by %r: playcount=%r listeners=%r",
                    track_name,
                    artist_name,
                    record.get("playcount"),
                    record.get("listeners"),
                )
                continue

#:             --------------------------------------------------------------
#: NE: Bilesik anahtar. docs/SCHEMA.md'de PK (snapshot_date, artist_name, track_name);
#:     snapshot_date tek kosuda sabit oldugu icin burada iki bilesen yetiyor.
#:
#:     Tekrar neden mumkun? Chart sayfalar cekilirken yeniden siralanabilir; ayni parca
#:     hem 1. hem 2. sayfada gorunebilir. Gozlemlenmedi ama curutulmedi de - PROGRESS
#:     "acik sorular"da duruyor. Burasi o riskin karsilandigi yer.
#:
#:     "Ilki kazanir" karari: sayfalar sirali geldigi icin ilk gorulen KUCUK rank'a
#:     sahiptir. Sonrakini tutsaydik ayni parca daha kotu bir sirayla kaydedilirdi.
#:
#: KANIT: (ayni sayfayi iki kez ver -> ikincisinin tamami atilir)
#:   uv run python -c "
#:   import json, logging; logging.basicConfig(level=logging.INFO)
#:   from lastfm_etl.transform import transform_chart
#:   p = json.load(open('tests/fixtures/lastfm/chart_gettoptracks_success.json'))
#:   print(len(transform_chart([p, p]).tracks))   # 20, 40 degil
#:   "
            key = (artist_name, track_name)
            if key in seen:
                dropped += 1
                logger.warning(
                    "dropped a repeat of %r by %r; the earlier rank wins",
                    track_name,
                    artist_name,
                )
                continue
            seen.add(key)

            duration = _to_int(record.get("duration"))
            tracks.append(
                {
                    "snapshot_date": snapshot,
                    "rank": _rank(attr, index),
                    "track_name": track_name,
                    "artist_name": artist_name,
                    "playcount": playcount,
                    "listeners": listeners,
                    "duration_seconds": (
                        None if duration == UNKNOWN_DURATION else duration
                    ),
                    "track_mbid": _text(record.get("mbid")),
                    "track_url": _text(record.get("url")),
                    "ingested_at": ingested,
                }
            )

#:             --------------------------------------------------------------
#: NE: artists satiri tracks satirinin ICINDEN degil, ayni kayittan uretiliyor - ama
#:     KRITIK NOKTA: artist_name degiskeni ikisinde de AYNI degisken. tracks'e yazilan
#:     ad ile artists'e yazilan ad ayni bellekteki ayni string. FK butunlugu bu yuzden
#:     bir kontrol degil, bir OLGU.
#:
#:     Bu satir ancak dedup kontrolunden SONRA calisir. Tersi olsaydi, atilan bir
#:     satirin sanatcisi artists tablosuna girer ve hicbir tracks satirinin isaret
#:     etmedigi bir dimension satiri olusurdu - "orphan dimension". Zararsiz gorunur,
#:     JOIN'i bozmaz, ama tablo artik yalan soyler.
#:
#: BIZDE: Olculdu - success fixture'inda 20 parca, 6 sanatci. Yani setdefault 14 kez
#:     "zaten var" deyip geciyor.
            # setdefault, not an if: the first occurrence of an artist wins, and the
            # first occurrence is the one with the best rank because pages are ordered.
            artists.setdefault(
                artist_name,
                {
                    "snapshot_date": snapshot,
                    "artist_name": artist_name,
                    "artist_mbid": _text(artist.get("mbid")),
                    "artist_url": _text(artist.get("url")),
                    "ingested_at": ingested,
                },
            )

#:     ----------------------------------------------------------------------
#: NE: Kosunun tek ozet satiri. Uc sayi: kac satir uretildi, kac sanatci, kac satir
#:     atildi. Atilan satirlarin her biri zaten WARNING basti; bu satir "toplamda ne
#:     oldu" sorusunun cevabi.
#:
#:     Neden onemli: sessiz eleme, veri hattinin en tehlikeli davranisidir. 100 satir
#:     bekleyip 60 alan bir tabloyu kimse fark etmez - ta ki bir rapor tuhaf gorunene
#:     kadar. "3 rows dropped" satiri, o gunu aylar sonra teshis edebilmenin tek yolu.
#:
#:     %s kullanimi f-string degil: log seviyesi kapaliysa formatlama HIC yapilmaz.
#:     len() cagrilari yine de calisir - lazy olan formatlama, argumanlar degil.
#:
#: BIZDE: P2.4'te bu satir bir teste donusecek: "bozuk fixture ver, dropped sayisini
#:     dogrula". Log satiri gozlemlenebilirligin, test edilebilirligin degil, ama
#:     ikisi de ayni seyi olcuyor.
    logger.info(
        "%s tracks, %s artists, %s rows dropped",
        len(tracks),
        len(artists),
        dropped,
    )
    return ChartTables(tracks, list(artists.values()))

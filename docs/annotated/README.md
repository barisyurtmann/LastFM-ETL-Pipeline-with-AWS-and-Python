# `docs/annotated/` — kodun yorumlu aynası

Bu klasör, `src/` altındaki her `.py` dosyasının **satır satır Türkçe yorumlanmış
kopyasını** tutar. Amaç tek: kodu okurken açıklamayı başka bir dosyada aramamak.

```
src/lastfm_etl/config.py            <- gerçek kod. İngilizce, temiz, portfolyo.
docs/annotated/src/lastfm_etl/config.py   <- aynısı + Türkçe ders yorumları.
```

Yol, `src/`'in **birebir aynası**: `docs/annotated/` önekini silersen gerçek dosyanın
yolunu bulursun. Eşleme kuralı yazmaya gerek kalmaz.

---

## Kural: `#:` işareti

| Satır | Anlamı |
|---|---|
| `#:` ile başlıyor | **Açıklamadır.** Gerçek dosyada yoktur |
| Başka her şey | Gerçek dosyayla **birebir aynıdır** — tek karakter bile fark yok |

Bu, iki dosyanın birbirinden sapmadığını **makineyle** doğrulamayı mümkün kılar:

```bash
# Çıktı boşsa iki dosya aynıdır. Bir şey basıyorsa ayna bayattır.
grep -v "^[[:space:]]*#:" docs/annotated/src/lastfm_etl/config.py \
  | diff - src/lastfm_etl/config.py
```

Kopyalanan doküman **her zaman** sapar; sapmayan kopya yoktur, sadece sapması ölçülen
kopya vardır. Yukarıdaki komut o ölçümdür.

---

## Yazım sözleşmesi (2026-08-20'de değişti)

**Eski kural — "kod bloğu başına en fazla 3 satır yorum" — kaldırıldı.**

Gerekçe: 3 satıra yalnızca **neden** sığıyordu. `Final çalışma zamanında bir şeyi
kilitlemez, yalnızca mypy'ye söyler` cümlesi, okuyanın *type hint*, *type checker*,
*mypy* ve *çalışma zamanı* kavramlarını bildiğini varsayar. Bilmiyorsa cümle bilgi
taşımaz, sadece kendine güvenli görünür. Bütçe, açıklamayı **hatırlatmaya** indirgiyordu.

Yeni sözleşme — her açıklama bu üç soruyu bu sırayla cevaplar:

| Katman | Soru |
|---|---|
| **NE** | Bu sözdizimi/nesne aslında nedir? Python bununla ne yapar? |
| **KANIT** | İddiayı doğrulayan, kopyalanıp çalıştırılabilir komut |
| **BİZDE** | Bizim kodda tam olarak neyi değiştiriyor? |

Ek kurallar:

- **Satır bütçesi yoktur.** Kavram anlaşılana kadar yazılır.
- **Ön koşul kavramlar dosyanın başına.** `class`/`instance`, dunder metotlar, kalıtım
  gibi *aşağıdaki her şeyin üzerine kurulduğu* konular satır aralarına serpiştirilmez;
  dosyanın en üstünde numaralı bir **Bölüm 0** olarak durur. Sebep: bunlar tek bir satıra
  ait değil, dosyanın tamamına aittir.
- **Ölçülmemiş iddia yazılmaz.** "Şu hata tipini verir" diyorsan çalıştırıp görmüş
  olacaksın. Ölçüm bir notu yalanlarsa **düzeltme aynaya yazılır ve not düzeltilir**.

---

## Kurallar

1. **Ayna, kaynağıyla aynı commit'te güncellenir.** Kod değişip ayna değişmediyse
   ayna yalan söylüyordur ve yalan söyleyen doküman, dokümansızlıktan kötüdür.
2. **Bu dosyalar çalışmaz, import edilmez, pakete girmez.** `src/` dışında oldukları
   için `pyproject.toml` onları paketlemez. `pytest` de toplamaz (`test_*.py` değiller).
3. **Türkçe yorum yalnızca burada serbesttir.** `src/` altındaki kod İngilizcedir ve
   orada yorum yalnızca **neden**i anlatır, **ne yaptığını** değil.
4. **Yeni bir `.py` yazıldığında aynası da yazılır.** Aynasız kalan modül, altı ay
   sonra "burada ne oluyordu" diye bakılan modüldür.

---

## Bu klasör `notes/` ile nasıl bölüşüyor

| Soru | Nerede |
|---|---|
| Bu satır ne yapıyor, kullandığı dil aracı **nedir** — ilk öğrenme | `docs/annotated/` |
| Aynı konular altı ay sonra, **hatırlatma** tablosu + kanıt komutları | `docs/notes/19` |
| Bu **tasarım** neden böyle? (fail-fast, sır sızıntısı, araç seçimi) | `docs/notes/18` |
| Bu **karar** neden geri alınamaz? | `docs/adr/` |

Sınır artık "özel bilgi / genel bilgi" değil — çünkü genel bilgiyi de kodun yanında
öğrenmek gerekiyor. Yeni sınır **öğretme / hatırlatma**: ayna öğretir (uzun, örnekli),
`notes/19` hatırlatır (tablo, tek cümle). Aynı konu iki yerde geçerse **ayna kaynaktır**,
not ondan türetilir.

---

## İçindekiler

| Ayna | Satır | Kapsadığı konular |
|---|---|---|
| [`src/lastfm_etl/config.py`](src/lastfm_etl/config.py) | ~550 | **Bölüm 0:** modül/import anı, class-instance-`self`, dunder metotlar, kalıtım, exception ve `raise`, docstring. **Bölüm 1:** PEP 8 import sırası, logging (Logger/Handler/Level, `__name__`), type hint + `Final` + `tuple[str, ...]` + mypy, `RuntimeError` kalıtımı, `@dataclass`ın ürettiği kod, `frozen`/`slots`/`repr=False`, `__post_init__`, `fields()`, `getattr`, `.strip()`, `", ".join()`, maskeli `__repr__`, `lru_cache` sarmalayıcısı, ortam değişkeni nedir, `find_dotenv`/`override=False`, `%s` logging |
| [`src/lastfm_etl/extract/api.py`](src/lastfm_etl/extract/api.py) | ~745 | **Bölüm 0:** exception nesnesi ve `raise`, `except`in kalıtımla eşleşmesi, `try/except/as/from` ve zincirleme, decorator'ın ne olduğu, keyword-only `*`, `frozenset` + `in` tuzağı, `requests` Session/Response ve `raise_for_status`'ın neden yokluğu. **Bölüm 1:** `from __future__ import annotations`, PEP 8 import sırası, tenacity'nin beş parçası, `Final`, `(connect, read)` timeout, retry bütçesi, hata taksonomisi, dar `try` kuralı, gövde-status sırası, `!r`, `.get()` vs `[]`, `%s` logging, `or` ve mutable default argument tuzağı |

---

## Bilinen borç

- **`ruff` kurulduğunda** (ROADMAP → Sonraki tur) bu klasör `exclude` listesine girmeli;
  aksi halde linter, ders yorumlarıyla dolu bir dosyayı üretim kodu sanıp uyarı yağdırır.
- **Sapma kontrolü şimdilik elle çalıştırılıyor.** P2.4'te `pytest` geldiğinde bu bir
  teste dönüşebilir: aynadan `#:` satırlarını sil, kaynakla karşılaştır, eşit değilse
  testi düşür. O zaman ayna bayatlarsa CI söyler, insan hafızası değil.
- **Aynadaki kanıt komutları da bayatlayabilir.** Bugün hiçbiri otomatik çalışmıyor;
  aynı `pytest` turunda bunların bir kısmı doctest'e dönüştürülebilir.

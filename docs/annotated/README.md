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
| Bu **satır** ne yapıyor? | `docs/annotated/` — kodun yanında |
| Bu **tasarım** neden böyle? (fail-fast, sır sızıntısı, araç seçimi) | `docs/notes/18` |
| Bu **sözdizimi** genel olarak nasıl çalışır? (hızlı referans, kanıt komutları) | `docs/notes/19` |
| Bu **karar** neden geri alınamaz? | `docs/adr/` |

Aynı bilgiyi iki yere yazmamak için: ayna dosyası **bu koda özel** olanı anlatır,
`notes/` **başka projede de geçerli** olanı. Sınır bu.

---

## İçindekiler

| Ayna | Kaynak | Kapsadığı konular |
|---|---|---|
| [`src/lastfm_etl/config.py`](src/lastfm_etl/config.py) | `src/lastfm_etl/config.py` | modül docstring'i, PEP 8 import sırası, `getLogger(__name__)`, `Final`, `tuple[str, ...]`, `RuntimeError` kalıtımı, `dataclass(frozen/slots/repr)`, `__post_init__`, `fields()` + `getattr`, maskeli `__repr__`, `lru_cache`, `find_dotenv`/`override=False`, comprehension'lar, örtük string birleştirme, `%s` logging |

---

## Bilinen borç

- **`ruff` kurulduğunda** (ROADMAP → Sonraki tur) bu klasör `exclude` listesine girmeli;
  aksi halde linter, ders yorumlarıyla dolu bir dosyayı üretim kodu sanıp uyarı yağdırır.
- **Sapma kontrolü şimdilik elle çalıştırılıyor.** P2.4'te `pytest` geldiğinde bu bir
  teste dönüşebilir: aynadan `#:` satırlarını sil, kaynakla karşılaştır, eşit değilse
  testi düşür. O zaman ayna bayatlarsa CI söyler, insan hafızası değil.

# 24 — Generator, `yield` ve tembel değerlendirme

> **Kısa cevap** — `return list` yerine ne zaman `yield`?
>
> 1. `yield` içeren fonksiyon çağrıldığında **çalışmaz**; bir generator nesnesi döndürür.
>    Gövde ancak tüketildikçe (`for`, `next()`) parça parça çalışır ve `yield`'de **durur**.
> 2. Kazancı bellek; bedeli **kısmi durum** — hata iterasyonun ortasında çıkar, çağıran
>    işin yarısını çoktan yapmış olur.
> 3. Eşik nettir: sonuç belleğe sığıyorsa `list`, sığmıyorsa generator. "Daha şık" bir
>    gerekçe değildir.

## Neden

Bir fonksiyonun dönüş tipi, çağıranın **hata anında hangi durumda olacağını** belirler.
`list` döndüren fonksiyon dönene kadar çağırana hiçbir şey vermez: ya hepsi ya hiçbiri.
Generator ise veriyi akıtır — 3. sayfada patlarsa ilk iki sayfa çoktan işlenmiş, belki
S3'e yazılmıştır. Bu bir hata değil, bir **trade-off**; ama bilmeden seçilirse hata olur.

İkinci tuzak: generator **tek kullanımlıktır**. `len()` çalışmaz, ikinci kez dolaşılamaz.
Bir fonksiyonu `list` → generator'a çevirdiğin gün çağıran kod sessizce boş liste görmeye
başlayabilir.

## Nasıl

Bizim `fetch_top_tracks_pages` generator olarak şöyle yazılırdı:

```python
def iter_top_tracks_pages(
    config: Config, *, target: int = 100, page_size: int = 50,
    max_pages: int = 10, session: requests.Session | None = None,
) -> Iterator[dict[str, Any]]:          # list[...] degil: Iterator/Iterable/Generator
    session = session or requests.Session()
    collected = 0
    for page in range(1, max_pages + 1):
        payload = fetch_top_tracks(config, limit=page_size, page=page, session=session)
        records = _track_records(payload)
        if not records:
            break
        yield payload                    # BURADA DURUR, cagiran devam edince buradan surer
        collected += len(records)
        if collected >= target:
            break
```

`yield`'den **sonraki** satırlar çağıran bir sonraki elemanı isteyene kadar çalışmaz.
Çağıran ortada `break` ederse `collected += ...` hiç çalışmaz, kapanış log'u hiç basılmaz,
`session` kapanmaz. Generator'da "fonksiyonun sonu" garanti değildir.

| | `list[dict]` | `Iterator[dict]` |
|---|---|---|
| Bellek | hepsi bellekte | sayfa sayfa |
| Hata anı | veri çağırana geçmeden | iş yarıda kalmış olarak |
| `len()`, tekrar dolaşma | çalışır | çalışmaz, tek kullanımlık |
| Test | `len(pages) == 2` | önce `list(...)` ile tüketmek gerekir |

## Kanıt

```bash
uv run python -c "
def g():
    print('1. sayfa uretildi'); yield 'a'
    print('2. sayfa uretildi'); yield 'b'
it = g()
print('cagrildi, hicbir sey basilmadi ->', type(it).__name__)
print(next(it))
print(list(it))
print(list(it))   # [] -> generator tek kullanimlik
"
```

## Mülakat cevabı

*"Sayfalı çekimde neden liste döndürdün, generator değil?"*

Liste döndürdüm çünkü veri seti sınırlı (100 kayıt, 2 sayfa) ve hatanın **atomik** olmasını
istedim: fonksiyon dönene kadar çağırana hiçbir sayfa geçmiyor, dolayısıyla yarım yazılmış
bir koşu oluşamıyor. Generator'ın tek gerçek kazancı bellek ve burada kazanç sıfır, bedeli
kısmi durum yönetimi. Eşiği de söyleyebilirim: sonuç belleğe sığmadığı anda generator'a
geçerim — `boto3`'ün `get_paginator()`'ı milyonlarca S3 nesnesi için tam olarak bunu yapar,
sayfa sayfa `yield` eder.

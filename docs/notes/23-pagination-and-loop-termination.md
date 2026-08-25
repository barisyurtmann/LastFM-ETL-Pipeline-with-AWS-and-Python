# 23 — Sayfalama: döngü nerede durur, ne döndürür

> **Kısa cevap** — Sayfalı bir API'den N kayıt çekerken döngü ne zaman durmalı?
>
> 1. **Aldığın kaydı say, sayfa sayısını hesaplama.** `ceil(N / page_size)` sunucunun
>    istediğin sayfa boyutuna uyduğunu varsayar; uymadığında veri **sessizce** eksik gelir.
> 2. Tek koşul yetmez: *hedefe ulaştım* + *boş sayfa geldi* + *sayfa tavanı*, üçü birden.
> 3. Sayfaları **birleştirmeden** döndür. Sayfa metadata'sı (kaçıncı sayfa, sayfa boyutu)
>    veriyi yorumlamak için gerekebilir; birleştirme onu geri gelmeyecek şekilde siler.

## Neden

Sayfalı API'lerin sinsi özelliği: **eksik veri bir hata değildir.** Sunucu istediğinden az
kayıt döndürdüğünde HTTP 200 döner, hata belgesi yoktur, istemci "başarılı" görür.
Aritmetiğe dayanan döngü o eksik veriyi diske yazar; snapshot türü kaynaklarda geriye
dönük çekilemediği için de geri gelmez.

İkinci kırılma noktası sonsuz döngü: "hedefe ulaşana kadar" koşulu hedefe hiç
ulaşılamadığında hiç durmaz. Serverless'ta faturası, timeout'a kadar para yakıp hiçbir şey
yazmadan ölmektir.

## Nasıl

| Durma koşulu | Rolü | Tek başına yeter mi |
|---|---|---|
| `collected >= target` | Asıl amaç | Hayır — kaynak yetersizse hiç tetiklenmez |
| Gelen sayfa boş | Kaynak tükendi | Hayır — sunucu aynı sayfayı tekrarlarsa tetiklenmez |
| `max_pages` tavanı | Son savunma hattı | Doğru sonuç vermez ama **durmayı garanti eder** |

Genel kalıp: **açık uçlu her döngüde, mantık doğru çalışsa bile çalışmasını beklemediğin
bir tavan bulunur.** Tavana çarpmak bir hata değil, bir *sinyaldir* — `WARNING` basar.

Python'da bu üçlüyü fazladan bayrak değişkeni tutmadan yazmanın yolu `for`/`else`:
`else` bloğu yalnızca döngü **hiç `break` görmeden** bittiğinde çalışır.

```python
for page in range(1, max_pages + 1):
    records = fetch(page)
    if not records:
        break
    collected += len(records)
    if collected >= target:
        break
else:
    logger.warning("ceiling hit with %s of %s", collected, target)
```

Sayfa boyutunu hedefin **altında** seç (bizde 50 / 100). Eşit seçersen döngü her koşuda
tam bir tur döner: sayfalama kodu üretimde hiç sınanmaz ve gerçekten gerektiği gün ilk
kez çalışır. İlk kez çalışan kod çalışmaz.

## Kanıt

```bash
uv run python -c "
for i in range(3):
    if i == 5: break
else:
    print('break gormedi -> else calisti')
for i in range(3):
    if i == 1: break
else:
    print('bu satir hic basilmaz')
"
```

## Mülakat cevabı

*"Sayfalı bir kaynaktan çekerken döngüyü nasıl sonlandırırsın?"*

Döngüyü sunucunun bildirdiği sayıya değil **fiilen aldığım kayıt sayısına** bağlarım; çoğu
API eksik sayfayı hata olarak bildirmez, aritmetik durma koşulu o gün sessizce kısa veri
üretir. Yanına iki koruma: boş sayfada dur, ve ulaşılması beklenmeyen bir sayfa tavanı —
tavan doğruluk için değil, timeout faturası için vardır. Trade-off: tavana çarpan koşu
exception yerine `WARNING` ile eksik veri döndürür, hata log'da kalır. Alerting'i olan bir
sistemde tavanı sert hata yapardım.

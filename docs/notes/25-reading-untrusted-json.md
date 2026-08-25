# 25 — Dış dünyadan gelen JSON'u okumak

> **Kısa cevap** — Bir API payload'ını koda çevirirken hangi refleksler?
>
> 1. **`[]` mi `.get()` mi?** Anahtarın varlığı *senin* garantinse `[]` (yoksa bu bir
>    bug'dır, gürültülü patlamalı). Anahtar *dış dünyadan* geliyorsa `.get()` ve yokluğu
>    bir **veri durumu** olarak ele al.
> 2. **"Yok"un birden çok kılığı vardır**: anahtar yok / `null` / boş string / boşluk /
>    `"0"` gibi sentinel değerler. Hepsini tek bir `None`'a indirgeyen **tek bir fonksiyon**
>    yaz, her çağrı yerinde tekrar etme.
> 3. **Bozuk kayıt politikası yazılı olmalı**: at, null'la, yoksa patlat. Yazılı değilse
>    politika yoktur — sadece o gün yazılmış bir `if` vardır.

## Neden

JSON'un tipi yoktur, **değeri** vardır. `json.load()` sana `dict | list | str | int |
float | bool | None` döndürür ve hangisi olduğunu sunucu belirler, sen değil. Tip varsayımı
yapan her satır, sunucunun bir gün fikrini değiştirmesiyle `TypeError`'a döner.

İkinci kırılma: **sessiz yanlış**. `len(row["track"])` satırı, `track` bir liste yerine
tek nesne geldiğinde patlamaz — sözlüğün *anahtar sayısını* sayar. Yanlış sayı, hata yok.
Gürültülü yanlış, sessiz yanlıştan her zaman ucuzdur.

## Nasıl

| Kalıp | Ne çözer |
|---|---|
| `value if isinstance(value, dict) else {}` | Beklenen tip gelmediğinde alt okumaların patlamaması; `None.get()` yerine boş sözlük |
| Tek bir `_text()` yardımcısı | "Yok"un üç kılığını (anahtar yok / boş / boşluk) tek `None`'a indirger |
| `_to_int()` — `try` yalnızca `int()` çağrısını sarar | `try` ne kadar genişse hatanın nereden geldiği o kadar belirsizdir |
| Sentinel değeri **isimlendir** (`UNKNOWN_DURATION = 0`) | `if x == 0` okuyana "sıfır" der; sabit adı "bilinmiyor" der. Aynı sayı, iki anlam |
| XML kökenli JSON'da tek elemanlı liste kontrolü | XML'de "tek elemanlı liste" yoktur; tek kayıt kaldığında liste sessizce nesneye çöker |

**Yakalanmayan hata tipi bir iddiadır.** `_to_int` içinde `TypeError` yakalanmıyor, çünkü
`_text` zaten `str` olmayanı elemiş — buraya `str` dışı bir şey *ulaşamaz*. O iddia bir gün
yanlış çıkarsa gürültülü patlamasını istiyoruz. Her hatayı yakalamak, hiçbirini yakalamamak
kadar kötüdür.

**Türetilmiş alanlar girdiden okunur, kendi ayarından değil.** `rank`'i hesaplarken sayfa
boyutunu bizim `DEFAULT_PAGE_SIZE` sabitimizden değil sunucunun `@attr`'ından okuyoruz.
Sabit yazılsaydı, config değişip cevap değişmediği gün sıra sessizce kayardı.

**Tekilleştirme için `set`, "ilk gören kazanır" için `dict.setdefault`.** İkisi de aramayı
eleman sayısından bağımsız hale getirir; `set`'e ve `dict` anahtarına yalnızca **hashable**
(değişmez) nesne konur — `tuple` olur, `list` olmaz.

## Kanıt

```bash
uv run python -c "
print(len({'name':'x','playcount':'9'}))   # 2 <- liste sanip len() cagirmanin sonucu
print(isinstance(True, int))               # True <- bool int'ten turer
d={}; d['z']=1; d['a']=2; print(list(d))   # ['z','a'] <- dict EKLEME sirasini korur
try: {['a']}
except TypeError as e: print('hashable degil:', e)
"
```

## Mülakat cevabı

*"Bir API'nin JSON cevabını nasıl güvenli parse edersin?"*

Payload'ın şemasını garanti kabul etmem: her alanı `.get()` ile okur, beklenen tipi
`isinstance` ile kapıda kontrol ederim; "yok" kavramının o kaynaktaki bütün kılıklarını tek
bir yardımcıda `None`'a indirger, böylece politikayı tek yerde tutarım. Kritik olan ayrımı
baştan yaparım: **bozuk bir satır** atılır ve loglanır, **bozuk bir sayfa** koşuyu durdurur —
çünkü ikincisinde arkasındaki bütün türetilmiş alanlar da yanlış olur. Trade-off: satır atmak
sessiz veri kaybı riski taşır, o yüzden atılan sayıyı koşu sonunda tek bir `INFO` satırında
raporlarım. Alerting'i olan bir sistemde bu sayıya eşik koyardım.

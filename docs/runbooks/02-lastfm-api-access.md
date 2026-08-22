# 02 — Last.fm API erişimi: key, ilk çağrı, fixture'lar

**Son doğrulama:** 2026-08-22 (geriye dönük yazıldı — kaynak: ADIM 1 ölçüm kayıtları, `notes/11`)
**Süre:** ~60 dk · **Sıklık:** key başına bir kez; keşif adımları yeni endpoint eklendiğinde
**Kapsam:** ROADMAP adım **1** (1.1–1.8)

**Bitiş durumu:**

- Last.fm API key alınmış, `.env`'e yazılmış, git'e sızmamış
- Mutlu yol **ve** hata yolları ölçülmüş (tahmin değil, kaydedilmiş çıktı)
- `tests/fixtures/lastfm/` altında gerçek payload'lar duruyor — testler ağsız çalışabilir

> **Geriye dönük not:** Adım 1'in ölçüm **sonuçları** PROGRESS'e kaydedilmiş, ama bazı
> komutların birebir metni kaydedilmemiş. Aşağıda ⚠ ile işaretli komutlar **yeniden
> üretilmiş** tariflerdir: aynı sonucu verirler, ama o gün yazılan satırın kopyası değildir.
> Bu ayrımı koruyorum — runbook'un uydurmadığını bilmen bir şey ifade eder.

---

## Bölüm 1 — API key al

1. https://www.last.fm/api/account/create
2. Last.fm hesabıyla giriş yap (yoksa aç)
3. Formu doldur: uygulama adı, açıklama, (varsa) callback URL — kişisel kullanım için
   callback boş bırakılabilir
4. Sonuç ekranında **API key** ve **shared secret** verilir

> **`shared_secret` bu projede kullanılmıyor** ve `.env`'e yazılmıyor. Sebep: yalnız public
> chart metodları çağrılıyor. `api_key` **kimliktir**; `shared_secret` yazma/kullanıcı
> işlemleri için imza (`api_sig`) üretmeye yarar — **yetki kanıtıdır**. Kullanılmayan bir
> sırrı saklamak gereksiz risktir.

`.env`'e yaz:

```
LASTFM_API_KEY=<gerçek key>
```

**Doğrulama:**

```bash
git status --short          # .env görünmemeli
git check-ignore -v .env    # eşleşme göstermeli
```

---

## Bölüm 2 — Sırrı oturuma yükle

Anahtar **komut satırına elle yazılmaz** — shell geçmişine (`.bash_history`, PowerShell'de
PSReadLine dosyası) kalıcı olarak düşer.

**Git Bash / Linux / macOS:**

```bash
set -a
source .env
set +a
```

| Parça | Ne yapar |
|---|---|
| `set -a` | Bundan sonra atanan **her** değişkeni otomatik `export` et (alt süreçler görsün) |
| `source .env` | Dosyayı **mevcut** kabukta çalıştır (`bash .env` alt kabukta çalışır, işe yaramaz) |
| `set +a` | Otomatik export'u kapat |

**PowerShell:**

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
  }
}
```

**Doğrulama** — değeri basmadan:

```bash
echo ${#LASTFM_API_KEY}     # 32 gibi bir uzunluk; 0 ise yüklenmemiş
```

---

## Bölüm 3 — İlk çağrı

**Base URL:** `http://ws.audioscrobbler.com/2.0/`
**Auth modeli:** query parametresinde API key (`api_key=...`) — header yok, OAuth yok

⚠ *Aşağıdaki komut şablonu `notes/11`'den; adım 1.2'de atılan birebir satır kayıtlı değil.*

```bash
curl -sS "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=$LASTFM_API_KEY&format=json&limit=20"
```

PowerShell'de:

```powershell
curl.exe "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=$env:LASTFM_API_KEY&format=json&limit=20"
```

| Kural | Sebep |
|---|---|
| **URL'yi çift tırnak içine al** | `&` cmd/PowerShell'de komut ayırıcıdır. Tırnaksız URL kısmen çalışır ve `format=json` **sessizce kaybolur** |
| PowerShell'de **`curl.exe`** yaz | PowerShell 5.1'de `curl` bir alias'tır, `Invoke-WebRequest`'e çözülür — bayrakları farklıdır. Teşhis: `Get-Command curl` |
| Değişken adı kullan, değeri değil | Anahtar geçmişe düşmesin (tam çözüm değil — süreç argümanı olarak yine görünür) |

---

## Bölüm 4 — Hata yollarını ölç

**Bu bölüm atlanamaz.** İstemci kodunun (P2.1) hata yönetimi buradan çıkacak; tahminle
yazılan hata yolu, üretimde ilk kırılan yerdir.

Dört deney — hepsi bu projede fiilen ölçüldü:

| Deney | Status | `Content-Type` | Gövde |
|---|---|---|---|
| `format` parametresi **yok** | **200** | `text/xml` | `<` ile başlıyor |
| `format=json` | 200 | `application/json` | `{` ile başlıyor |
| **Bozuk `api_key`** | **403** | `application/json` | `{"message":"Invalid API key...","error":10}` |
| **Bozuk `method`** | **400** | `application/json` | `{"message":"Invalid Method...","error":3}` |

Header'ları görmek için `-D -` ekle:

```bash
curl -sS -D - -o /dev/null "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=BOZUK&format=json"
```

**Çıkan üç ders:**

1. **`format=json` opsiyonel değil, zorunlu.** Unutulursa XML gelir, status yine 200'dür,
   `raise_for_status()` sessiz kalır ve `.json()` `JSONDecodeError: char 0` ile patlar —
   mesaj sorunu anlatmaz. Teşhis için `response.status_code` ve `response.text[:200]`'e bak.
2. **`raise_for_status()` tek başına yetmez.** Hem status hem gövde kontrol edilmeli.
3. **Gövde status'tan önce okunmalı.** `raise_for_status()` fırladığı anda akış kopar ve
   `error` kodunu (10, 3, 26...) taşıyan gövde okunmadan kaybolur. Retry kararı o koda
   bakacak.

> **Ölçüm bir varsayımı çürüttü:** "Last.fm hatalarda da 200 döner" iddiası yaygındır ve
> bu projede de başta öyle yazılmıştı. Ölçüm 403 ve 400 gösterdi. Doküman ölçümle düzeltildi.

---

## Bölüm 5 — Sayfalama ve `limit` davranışı

```bash
curl -sS "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=$LASTFM_API_KEY&format=json&limit=100&page=1"
```

Ölçülen `@attr` değerleri:

| `limit` | `perPage` | `totalPages` | `total` |
|---|---|---|---|
| 20 | 20 | 500 | 10000 |
| 100 | 100 | 100 | 10000 |

Üç sonuç:

- `total: 10000` gerçek bir sayım değil, **sabit bir tavan**
- `limit` sunucunun `perPage`'ini değiştiriyor → istemcide `perPage`'i sabit **yazma**,
  `@attr`'dan oku
- `rank` = `(page - 1) * perPage + index` — **her sayfa kendi `@attr.page`'iyle** hesaplanır

> **Tuzak:** Sayfaları birleştirip baştan `enumerate` etmek. Bu projede son sayfa 20 değil
> **19** kayıt döndürdü; global numaralama bütün sıraları kaydırırdı.

---

## Bölüm 6 — Fixture'ları kaydet

> **Fixture** = testlerin kullanacağı, diske kaydedilmiş gerçek API cevabı. Amacı: testlerin
> ağ olmadan, gerçek anahtar olmadan, her seferinde **aynı** veriyle çalışması.

Kaydedilen dosyalar — `tests/fixtures/lastfm/`:

| Dosya | İçerik |
|---|---|
| `chart_gettoptracks_success.json` | Mutlu yol, `page=1`, 20 parça (~31 KB) |
| `chart_gettoptracks_edge_cases.json` | `page=500` — eksik alanların çıktığı yer |
| `error_10_invalid_api_key.json` | Bozuk key cevabı |
| `error_3_invalid_method.json` | Bozuk method cevabı |

⚠ *Aşağıdaki kaydetme komutu yeniden üretilmiştir; o gün yazılan satır kayıtlı değil.
Sonuç aynıdır: pretty-printed, UTF-8 karakterleri kaçırılmamış JSON.*

```bash
mkdir -p tests/fixtures/lastfm

curl -sS "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=$LASTFM_API_KEY&format=json&limit=20&page=1" \
  | python -m json.tool --no-ensure-ascii \
  > tests/fixtures/lastfm/chart_gettoptracks_success.json
```

| Parça | Sebep |
|---|---|
| `python -m json.tool` | Pretty-print — tek satırlık JSON'un diff'i okunamaz |
| `--no-ensure-ascii` | Türkçe/Japonca sanatçı adları `ç` yerine gerçek karakter kalsın |

**Kenar durum fixture'ı** son sayfadan alınır — eksik alanlar orada yaşar:

```bash
curl -sS "...&limit=20&page=500" | python -m json.tool --no-ensure-ascii \
  > tests/fixtures/lastfm/chart_gettoptracks_edge_cases.json
```

**Doğrulama — anahtar sızmadı mı:**

```bash
grep -rn "api_key" tests/
```

**Çıktı boş olmalı.** Cevap gövdesi anahtarı içermez, ama bu kontrol yapılmadan fixture
commit'lenmez.

> **Ders (bu projede yaşandı):** İlk turda sadece mutlu yol fixture'ı kaydedildi. Şema
> tasarımına gelindiğinde eksik alanların hiç görülmediği fark edildi ve `page=500`
> sonradan eklendi. **Kenar durum fixture'ı baştan alınır** — API'ye ikinci kez gitmek
> her zaman mümkün olmayabilir.

> **`mbid` dersi:** "%21'i boş" sanıldı; ölçüm düzeltti — değer boş değil, **anahtar hiç
> yok**. `record["mbid"]` `KeyError` fırlatır. `.get("mbid")` kullan, `== ""` kontrolü yazma.

---

## Bölüm 7 — Rate limit

**Ölçülen:** Cevapta **hiçbir** rate-limit header'ı yok — ne `Retry-After`, ne `RateLimit-*`,
ne `X-RateLimit-*`.

```bash
curl -sS -D - -o /dev/null "http://ws.audioscrobbler.com/2.0/?method=chart.getTopTracks&api_key=$LASTFM_API_KEY&format=json" \
  | grep -i -E 'ratelimit|retry-after|x-rate'
```

⚠ *URL kısmı yeniden üretildi; PROGRESS'te `...` ile kısaltılmıştı. Sonuç kayıtlı: çıktı boş.*

**Belgelenen limit** (ikincil kaynak, bu projede **doğrulanmadı**): IP başına saniyede 5
istek, 5 dakikalık ortalama üzerinden.

**Aktif sondaj yapılmadı** — bilinçli. Limiti bulmak için hızlı istek atmak `error 26 —
API key banned` riski taşır ve anahtarı geri almak günler sürebilir. Header yoksa ve
doküman bir sayı veriyorsa, o sayının altında kal.

> Bu, istemci tarafında **üstel backoff + jitter** gerektirir: sunucu ne zaman tekrar
> deneyeceğini söylemiyorsa istemci kendi karar vermek zorunda. Detay → `notes/17`.

---

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `JSONDecodeError: ... char 0` | `format=json` eksik → XML geldi | URL'yi tırnakla, `format=json` ekle. `response.text[:200]`'e bak |
| Cevap geldi ama beklenen alanlar yok | `&` yüzünden parametrelerin bir kısmı kaybolmuş | URL'yi çift tırnak içine al |
| PowerShell'de tanınmayan bayrak | `curl` → `Invoke-WebRequest` alias'ı | `curl.exe` yaz |
| `error: 10` | Anahtar yanlış/boş | `echo ${#LASTFM_API_KEY}`; `.env`'i yeniden yükle |
| `error: 3` | Metod adı yanlış | `chart.getTopTracks` — büyük/küçük harf duyarlı |
| `error: 26` | **Anahtar banlandı** | İstek hızını düşür; Last.fm desteğine başvur. Bu yüzden aktif sondaj yapılmıyor |
| `echo ${#LASTFM_API_KEY}` → `0` | `source` alt kabukta çalıştırıldı | `source .env` (`bash .env` değil), aynı kabukta |

---

## Geri alma

| Durum | Ne yapılır |
|---|---|
| Anahtar sızdı (repoya girdi/paylaşıldı) | **Önce Last.fm'de anahtarı yenile**, sonra git geçmişini temizle. Sıra bu — geçmişi temizlemek sızmış anahtarı geçersiz kılmaz |
| Fixture eskidi / yanlış kaydedildi | Bölüm 6'yı tekrarla. Fixture'lar yeniden üretilebilir veridir, korunacak durum değil |
| Yanlış endpoint'e göre şema tasarlandı | Fixture'ı yeni endpoint'ten al, şema kararını ADR ile güncelle |

---

## Kaynaklar

- Last.fm API dokümanı: https://www.last.fm/api
- API key oluşturma: https://www.last.fm/api/account/create

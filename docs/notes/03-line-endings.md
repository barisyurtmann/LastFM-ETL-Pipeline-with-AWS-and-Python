# Satır Sonları (CRLF / LF) ve `.gitattributes`

> **Kısa cevap** — CRLF/LF farkı diff'i neden şişirir ve .gitattributes bunu tam olarak nasıl çözer?
>
> 1. Eklenen ve silinen satır sayısı birebir eşitse (1127/1127) içerik değil satır sonu değişmiştir.
> 2. Git varsayılanı "akıllı" değil "karışmaz"dır; kural yoksa CRLF'i olduğu gibi commit eder.
> 3. `add --renormalize` sadece index'i düzeltir, disk CRLF kalır; `rm -r --cached . && reset --hard` gerekir.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

## Problem nasıl ortaya çıktı

İki makinede çalışıyorum (ev + iş). Bir oturum başında `git status` şunu gösterdi:

```
9 files changed, 1127 insertions(+), 1127 deletions(-)
```

Eklenen ve silinen satır sayısı **birebir aynı**. Bu bir ipucu: içerik değişmemiş,
her satır "değişmiş" görünüyor. Sebep satır sonu karakteri.

Windows makinesi dosyaları CRLF (`\r\n`) ile yazmış, repoda ise LF (`\n`) duruyordu.

## Barış önce ne sandı

İlk bakışta bunun "sadece bir görüntü meselesi" olduğunu, Git'in kendi kendine
halledeceğini sandım. Halletmiyor — hiçbir kural verilmemişse Git dosyaya
dokunmaz, ne yazdıysan onu commit eder. Yani varsayılan davranış "akıllı" değil,
"karışmaz"dır.

İkinci yanlış varsayım: `.gitattributes` eklemenin mevcut dosyaları da düzelteceği.
Düzeltmiyor. Aşağıya bak.

## Git'in iki dönüşüm noktası

Git satır sonlarına iki yerde karışabilir:

- **`add`** sırasında: disk → repo
- **`checkout`** sırasında: repo → disk

| Kural | `add`'de | `checkout`'ta | Windows'ta diskte |
|---|---|---|---|
| `* text=auto eol=lf` | CRLF → LF | dokunmaz | LF |
| `* text=auto` | CRLF → LF | LF → CRLF | CRLF |
| `* -text` (veya kural yok) | dokunmaz | dokunmaz | ne yazdıysan |

Her üç durumda da **repo LF'tir** (ilk ikisinde). Fark sadece diskte ne gördüğün.

Bu projede `eol=lf` seçildi: disk ile repo aynı olsun. Gerekçe — dosya Docker'a
kopyalandığında, WSL'de açıldığında, CI'da okunduğunda hep aynı byte'lar olsun.
`text=auto` (CRLF'e çeviren sürüm) tarihsel varsayılandır ve LF anlamayan eski
Windows araçları içindi; bugünkü editörlerin böyle bir sorunu yok.

## Neden `git config` değil `.gitattributes`

| | Nerede yaşar | Kimi bağlar |
|---|---|---|
| `core.autocrlf` | makinede (`.git/config` veya global) | sadece o makineyi |
| `.gitattributes` | repoda, versiyonlu | repoyu klonlayan herkesi |

`.gitattributes`, `core.autocrlf`'i **ezer**. Yani bir makinede biri config'i
kurcalasa bile repo kuralı bozulmaz.

Genel kural: **makineye bağlı olan config'e, projeye bağlı olan repoya girer.**

## Yazılan dosya

```gitattributes
* text=auto eol=lf

*.parquet binary
*.png     binary
```

| Satır | Ne yapıyor |
|---|---|
| `text=auto` | Git dosyanın metin olup olmadığına içeriğine bakarak karar verir; metinse repoda LF'e normalize eder |
| `eol=lf` | Checkout'ta da LF bırakır, platforma göre CRLF'e çevirmez |
| `binary` | `-text -diff -merge` kısayolu. Binary dosyada tesadüfen geçen `0x0D 0x0A` dizisi eol filtresine yakalanırsa dosya bozulur |

`*.parquet` kuralı, henüz tek bir parquet dosyası yokken kondu. Kuralı dosya
gelmeden koymak doğru olan: sonradan eklersen arada bozulmuş bir dosya
commit'lenmiş olabilir.

## En önemli tuzak: `.gitattributes` mevcut dosyaları düzeltmez

Sıra ve her adımda ne olduğu:

| Adım | `git status` | Diskteki dosya |
|---|---|---|
| `.gitattributes` eklendi + commit | hâlâ kirli | CRLF |
| `git add --renormalize .` | **temiz** | hâlâ **CRLF** |
| `git rm -r --cached . && git reset --hard` | temiz | LF |

İkinci satır tehlikeli olan. `--renormalize` **index'i** düzeltir, diski değil.
`git status` temiz göründüğü için "çözüldü" sanılır, sonraki dosya kaydında CRLF
geri gelir. Diski zorla yeniden checkout etmek gerekir.

Uygulanan komut dizisi:

```bash
git add .gitattributes
git commit -m "chore: enforce LF line endings via .gitattributes"
git add --renormalize .
git rm -r --cached . >/dev/null && git reset --hard
```

`git reset --hard` commit edilmemiş her şeyi siler. Bu durumda güvenliydi çünkü
diff'in tamamı satır sonuydu — ama komut refleks hâline getirilecek bir komut değil.

## Doğrulama

```bash
git ls-files --eol docs/PROGRESS.md
```

Beklenen çıktı:

```
i/lf    w/lf    attr/text=auto eol=lf   docs/PROGRESS.md
```

| Alan | Anlamı |
|---|---|
| `i/` | index — repoda ne var |
| `w/` | working tree — diskte ne var |
| `attr/` | hangi kural uygulandı |

Üçü de `lf` diyorsa iş bitmiştir. `git status --short`'un boş olması tek başına
yeterli kanıt değil (yukarıdaki tuzak).

Asıl sınav: diğer makinede `git pull` yapınca diff'in geri gelmemesi.

## Prod'da ne kırılır

CRLF ile yazılmış bir shell script Linux konteynerine gittiğinde shebang satırı
`#!/bin/bash\r` olur. Kernel `/bin/bash\r` adında bir program arar ve bulamaz:

```
bad interpreter: No such file or directory
```

Dosya oradadır, mesaj yalan söylüyor gibidir. Adım 8.7'de `Dockerfile` yazılacağı
için bu soyut bir risk değil.

## Mülakat cevabı

> "Repoda satır sonlarını nasıl yönetiyorsun?"

Kısa cevap: `.gitattributes` ile `* text=auto eol=lf`. Gerekçe iki tane —
(1) `core.autocrlf` makine başına ayardır, ekip sözleşmesi olamaz;
(2) repo ile disk arasındaki fark bir gün Docker/CI tarafında shebang veya
line-ending hatası olarak patlar. Eklerken `git add --renormalize` yetmez,
working tree'yi de yeniden checkout etmek gerekir.

## Junior tuzağı

`git config --global core.autocrlf true` deyip "çözdüm" demek. Kendi makinende
diff kaybolur; takım arkadaşında, CI'da ve diğer makinende sürer. Kişisel ayarla
ekip problemi çözülmez.

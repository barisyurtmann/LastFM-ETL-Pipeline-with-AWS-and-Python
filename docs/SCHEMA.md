# Veri Sözleşmesi — curated katman

Bu dosya **yürürlükteki şemadır**: iki tablo, kolonları, tipleri, anahtarları.
Kararın *gerekçesi* ADR'de, *nerede olduğumuz* PROGRESS'te; burada yalnızca **sözleşme** var.

Kaynak: `chart.getTopTracks` · Grain: ADR-0005 (bir UTC günü = bir snapshot) ·
Kapsam: top 100 (ADR-0006) · Format: JSON Lines (P2.3) · Üretim: ADR-0016 (tek Lambda)

---

## `tracks` — fact tablosu

Bir satır = bir UTC gününde chart'ta görünen bir parçanın o andaki durumu.

**PK:** `(snapshot_date, artist_name, track_name)` · **Partition:** `snapshot_date`
**FK:** `artist_name` → `artists.artist_name`

| # | Kolon | Tip | Örnek | Null | Kaynak |
|---|---|---|---|---|---|
| 1 | `snapshot_date` | string (`YYYY-MM-DD`) | `"2026-08-25"` | hayır | *türetilmiş* — `datetime.now(UTC).date()` |
| 2 | `rank` | int | `1` | hayır | *türetilmiş* — `(page-1)*perPage + index + 1` |
| 3 | `track_name` | string | `"Petal"` | hayır | `track.name` |
| 4 | `artist_name` | string | `"Ariana Grande"` | hayır | `track.artist.name` — **FK** |
| 5 | `playcount` | int | `1114096` | hayır | `track.playcount` (str→int) |
| 6 | `listeners` | int | `120854` | hayır | `track.listeners` (str→int) |
| 7 | `duration_seconds` | int | `184` | **evet** | `track.duration` (str→int), `0 → null` |
| 8 | `track_mbid` | string | `"0f8c8467-a662-..."` | **evet** | `track.mbid` — anahtar payload'da olmayabilir |
| 9 | `track_url` | string | `"https://www.last.fm/music/Ariana+Grande/_/Petal"` | **evet** | `track.url` |
| 10 | `ingested_at` | string (ISO 8601 UTC) | `"2026-08-25T03:00:12Z"` | hayır | *türetilmiş* — `datetime.now(UTC)` |

## `artists` — dimension tablosu

Bir satır = bir UTC gününde chart'ta görünen bir sanatçı.

**PK:** `(snapshot_date, artist_name)` · **Partition:** `snapshot_date`

| # | Kolon | Tip | Örnek | Null | Kaynak |
|---|---|---|---|---|---|
| 1 | `snapshot_date` | string (`YYYY-MM-DD`) | `"2026-08-25"` | hayır | *türetilmiş* |
| 2 | `artist_name` | string | `"Ariana Grande"` | hayır | `track.artist.name` |
| 3 | `artist_mbid` | string | `"f4fdbb4c-e4b7-..."` | **evet** | `track.artist.mbid` |
| 4 | `artist_url` | string | `"https://www.last.fm/music/Ariana+Grande"` | **evet** | `track.artist.url` |
| 5 | `ingested_at` | string (ISO 8601 UTC) | `"2026-08-25T03:00:12Z"` | hayır | *türetilmiş* |

---

## Kurstan farklar ve sebepleri

| Kurs (Spotify) | Bizde (Last.fm) | Sebep |
|---|---|---|
| `album_df` | **yok** | `chart.getTopTracks` album döndürmüyor. Üç tablo yerine iki tablo; JOIN dersi duruyor |
| `artist_id` (PK, garantili) | `artist_name` (PK) | Last.fm `mbid`'i **garanti etmiyor** — ölçüm: 4/19 kayıtta anahtar yok. Garanti edilmeyen bir alan anahtar olamaz |
| `song_id` (PK) | `(snapshot_date, artist_name, track_name)` | Aynı sebep + grain günlük snapshot: aynı parça her gün bir kez daha görünür, tek `song_id` yeterli olmaz |
| `song_added` (datetime) | `snapshot_date` + `ingested_at` | Spotify "playlist'e eklenme" olayını saklıyor; bizde öyle bir olay yok. Yerine ölçümün ait olduğu gün ve ölçümün alındığı an |
| `popularity` (0-100 skor) | `playcount` + `listeners` | Last.fm ham sayaç veriyor, Spotify türetilmiş skor. Ham sayaç daha değerli: günlük artış iki snapshot'ın farkıdır |
| — | `rank` | Chart'ta sıra hiçbir alandan türetilemiyor (1.7'de ölçüldü). Materyalize edilmek zorunda |
| `duration_ms` | `duration_seconds` | Last.fm saniye veriyor. Birim **kolon adında** yazılı olmalı; `duration` tek başına yalan söyleyebilir |

**Tek cümlelik özet:** Spotify her varlığa kalıcı bir ID veriyor, Last.fm vermiyor.
Şemadaki bütün fark bu tek gerçekten çıkıyor.

---

## Verilen kararlar

**Surrogate key yok.** `artist_name` doğal anahtar olarak kullanılıyor; `sha1(artist_name)`
gibi türetilmiş bir ID üretilmedi. Gerekçe: 100 satır/gün ölçeğinde string JOIN'in maliyeti
yok ve fazladan kolon fazladan bakım demek. **Ne zaman gerekirdi:** sanatçı adı değişebilir
hale geldiğinde (SCD tip 2), ya da tablo birden çok kaynaktan besleniyorsa. O gün gelirse
ADR ile eklenir.

**`artist_mbid` `tracks`'ten çıkıp `artists`'e taşındı.** 1.7'de tek tablo tasarlandığı için
satır içindeydi. İki tablo olunca tekrar eden bir alan haline gelirdi — normalizasyon tam
olarak budur. Bilgi kaybolmuyor, JOIN'in arkasına geçiyor.

**`artist_url` geri geldi.** 1.7'de *"`artist_name`'den 39/39 türetilebiliyor"* diye
elenmişti. `artists` tablosunda satır başına bir kez duruyor, tekrar etmiyor.
**Alan eleme kararı tablo bazlıdır, global değil.**

**`track_url` ve `artist_url` nullable — 2026-08-25'te değişti.** Önce not-null yazılmıştı,
ölçülen veride de %100 dolu. Ama kod yazılırken görüldü ki bunu *zorlamanın* tek yolu, url'i
olmayan bir satırı **tamamen atmak** olurdu: anahtar da değil, metrik de değil, sadece
doğrulama linki. Bir görüntüleme alanı yüzünden gerçek bir chart satırını kaybetmek orantısız.
**Ders: şemada "not-null" bir dilek değil, bir taahhüttür.** Zorlayamayacağın bir taahhüdü
yazma — zorlanmayan not-null, dokümanla kodun sessizce ayrıştığı ilk yerdir.

**Tarihler string.** JSON'da tarih tipi yok (P2.3 kararı: JSON Lines). Athena tarafında
`snapshot_date` `string` görünecek; sorguda `date_parse` veya partition olarak kullanılacak.
Parquet'te bu bir `date` olurdu — formatın gerçek bedeli burada görünüyor.

**Bozuk kayıt politikası:**

| Durum | Davranış |
|---|---|
| `track.name` veya `track.artist.name` boş/yok | Satır **atılır** + `WARNING`. İkisi de PK bileşeni; null anahtarlı satır eksik satırdan kötüdür |
| `playcount` / `listeners` sayıya çevrilemiyor | Satır **atılır** + `WARNING`. Şemada not-null |
| `duration` çevrilemiyor veya `0` | `null`. Zaten nullable; `0` Last.fm'in "bilinmiyor"u |
| Aynı `(artist_name, track_name)` iki sayfada | **İlki** tutulur (küçük `rank`) + `WARNING` |

Atılan satır sayısı koşu sonunda tek `INFO` satırında raporlanır. Sessiz eleme yok.

**Aynı gün iki kez çalıştırılırsa:** aynı `snapshot_date=` partition'ının üzerine yazılır
(ADR-0016). Satır sayısı artmaz, son koşu kazanır.

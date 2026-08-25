# 26 — ETL mi ELT mi, ve ham katmanın bedeli

> **Kısa cevap** — Dönüşüm yüklemeden **önce** mi **sonra** mı?
>
> 1. **ETL:** Extract → Transform (uçuşta) → Load. Ham veri kalıcı olarak hiçbir yere
>    yazılmaz. **ELT:** Extract → Load (ham) → Transform. Modern bulut varsayılanı ELT.
> 2. Sıra bir stil tercihi değil, **hatayı geri alabilme** tercihi. Ham veri duruyorsa
>    yanlış transform "yeniden çalıştır"la düzelir; durmuyorsa o günün verisi gitmiştir.
> 3. ELT'yi ETL diye adlandırmak ikisini birden öğretmez. **Adı ne olduğu değil, ham
>    verinin diske inip inmediği belirler.**

## Neden

ETL'in "T ortada" olması bir tasarım tercihi değil, bir **kısıttı**: 1990'larda depolama
pahalıydı, ham veriyi saklamak savunulamazdı. S3'te 1 GB aylık birkaç sent olunca kısıt
kalktı ve sıra değişti.

Asıl mesele maliyet değil, **geri alınabilirlik**. Şemayı bugün tasarlıyorsun ve
yanılıyor olabilirsin — bu projede tam olarak yaşandı: `playcount`'un "tüm zamanlar
kümülatif" olduğu ancak ölçümle anlaşıldı. Ham veri duruyorsa düzeltme yeniden
çalıştırmaktır; durmuyorsa kalıcı veri kaybıdır.

## Nasıl

| | ETL | ELT |
|---|---|---|
| Ham veri | Kalıcı değil | Hedefte saklanır (raw / bronze katman) |
| Yanlış transform | O günler **geri gelmez** | Raw'a karşı yeniden çalıştırılır |
| Şema | Yazmadan önce bilinmeli (schema-on-write) | Sonradan değişebilir (schema-on-read) |
| Debug | Log + çıktı | Satırı üreten **tam payload** elde |
| Depolama | Az | Fazla (ama ucuz) |
| Tipik yer | Lambda/uygulama içi, dar pencere | S3 + dbt/Spark/warehouse |

**Katman isimleri:** raw/bronze (dokunulmamış), staging/silver (temizlenmiş),
curated/gold (iş mantığı uygulanmış). Buna **medallion mimarisi** deniyor — Databricks'in
popülerleştirdiği bir isimlendirme, bir standart değil.

**Kritik nüans — "yedek alıyorum" ELT'dir.** Ham payload'ın kalıcı bir kopyasını
tutuyorsan, diyagramda ne yazarsa yazsın raw katmanın vardır. Ayrım diyagramda değil,
diskte.

## Kanıt

Ölçülebilir bir komut değil, **doğrulanabilir bir soru**: *"Dünkü transform'da bir alanı
yanlış eşleştirdiğimi bugün fark ettim. Dünün verisini düzeltebilir miyim?"*
Cevap "evet" ise ELT yapıyorsundur. "Hayır" ise ETL.

Bu projede cevap **hayır** (ADR-0016), üstelik ikinci bir sebeple daha ağır:
`chart.getTopTracks` tarih parametresi almıyor, yani gün API'den yeniden çekilemiyor da.

## Mülakat cevabı

*"ETL mi ELT mi kullanırsın, neden?"*

Varsayılanım **ELT**: ham veriyi hedefte sakladığım için dönüşümü yanlış yaptığımda
yeniden çalıştırmak yetiyor, ve depolama bugün o sigortanın fiyatı yanında önemsiz.
**ETL'i şu koşullarda seçerim:** ham veriyi saklamanın yasal olarak yasak olduğu durumlar
(PII, KVKK/GDPR minimizasyon), veri hacminin saklamayı gerçekten pahalı yaptığı akış
işleri, ya da — bu projede olduğu gibi — referans mimarinin ETL olması ve öğrenme hedefinin
o olması. Trade-off'u net söylerim: ETL'de yanlış bir dönüşüm o günlerin verisini kalıcı
olarak kaybettirir, dolayısıyla **test artık iyi bir alışkanlık değil, tek emniyet ağıdır**.
Bu yüzden ETL seçtiğim her yerde dönüşümün test kapsamını ELT'dekinden yüksek tutarım.

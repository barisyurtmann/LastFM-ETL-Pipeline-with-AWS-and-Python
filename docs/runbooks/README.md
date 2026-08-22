# Runbook'lar

Bu klasör **prosedür** tutar: bir işi, düşünmeden, baştan sona tekrar edebilmek için.

> Sektör terimi: **runbook** — bir operasyonel işin adım adım, tekrarlanabilir tarifi.
> SRE/operasyon pratiğinde standart bir doküman türüdür. Gece 03:00'te uykulu bir insanın
> takip edebilmesi hedeflenir.

## Neden ayrı bir klasör

`docs/notes/` bir işin **ne** ve **neden**'ini anlatır; **nasıl**'ını değil. Not okuyup
"credential chain nedir" öğrenebilirsin ama iki ay sonra "AWS hesabını nasıl kurmuştum"
sorusunun cevabı orada yoktur. İki farklı soru, iki farklı doküman.

| Soru | Nereye |
|---|---|
| "Credential chain nedir?" | [`notes/`](../notes/README.md) |
| "Neden iki bucket açtık?" | [`adr/`](../adr/README.md) |
| **"AWS hesabını sıfırdan nasıl kurarım?"** | **buraya** |
| "Bu satır ne yapıyor?" | [`annotated/`](../annotated/README.md) |
| "Şu an neredeyiz?" | [`PROGRESS.md`](../PROGRESS.md) |

Ayırt edici test: **"Bu doküman bir eylem dizisi mi, yoksa bir bilgi mi?"** Eylem dizisiyse
runbook. Runbook okunmaz — **uygulanır.**

## Kurallar

1. **Her adım tek bir eylemdir.** "Kullanıcıyı oluştur ve MFA ata" iki adımdır.
2. **Her bölümün sonunda bir doğrulama vardır.** Doğrulaması olmayan adım, atlandığı fark
   edilmeyen adımdır.
3. **UI adımları eskir.** Her runbook başında **son doğrulama tarihi** yazar. Buton adı
   tutmuyorsa panik yok — kavramsal adım aynıdır, adı değişmiştir.
4. **Geri alma bölümü zorunlu.** "Yanlış yaptım, nasıl düzeltirim" cevapsız kalmaz.
5. **Sır yazılmaz.** Runbook "buraya secret'ı yapıştır" der, secret'ın kendisini taşımaz.
6. **Yapıldıktan sonra yazılır.** Yapılmamış bir prosedürün tarifi tahmindir.

## Şablon

```markdown
# NN — Başlık

**Son doğrulama:** YYYY-MM-DD · **Süre:** ~N dk · **Sıklık:** bir kez / her yeni makinede
**Bitiş durumu:** <bu runbook bitince neyin doğru olduğu>

## Ön koşullar
## Adımlar (bölüm bölüm, her bölüm sonunda doğrulama)
## Doğrulama (bütünsel)
## Sorun giderme
## Geri alma
```

## Numaralandırma

Numaralar **kronolojiktir**: projeyi baştan kurarken izlenecek sıra. `00` en sık
kullanılandır ve başa konur.

ADR'lerin aksine runbook'lar **immutable değildir** — UI değişince güncellenir, sıra
bozulursa yeniden numaralandırılabilir. (2026-08-22'de bir kez yapıldı: AWS runbook'u
`01` → `03`, çünkü repo kurulumu ve API erişimi ondan önce geliyor.)

## İçindekiler

| # | Konu | Sıklık | Adım |
|---|---|---|---|
| [00](00-new-machine-setup.md) | **Yeni makinede projeyi çalışır hale getirme**: `git clone`, `uv sync`, `.env`, AWS kimliği, beş doğrulama | Her yeni makinede | — |
| [01](01-repo-scaffold.md) | Sıfırdan iskelet: `git init`, `.gitignore`, `.gitattributes` + CRLF normalizasyonu, `pyproject.toml`, `src/` layout, `uv sync`, `.env.example`, README | Proje başına bir kez | Adım 0 |
| [02](02-lastfm-api-access.md) | Last.fm: key alma, `.env` yükleme, ilk çağrı, **hata yollarını ölçme**, sayfalama, fixture kaydetme, rate limit | Key başına bir kez | Adım 1 |
| [03](03-aws-account-bootstrap.md) | AWS: hesap, root MFA, budget alarm, IAM kullanıcı, kullanıcı MFA, access key, CLI, `aws configure` | Hesap: bir kez · CLI: her makinede | P1.2 |
| [04](04-s3-bucket-creation.md) | S3: isimlendirme kuralları, iki bucket, public access blok, versioning, tag, **key şeması** | Ortam başına bir kez | P1.3 |

**Sıfırdan kurulum sırası:** `01` → `02` → `03` → `04`. **Yeni makine:** yalnız `00`.

## Yazılacaklar (borç)

Şu an boş. Yeni bir konsol/terminal prosedürü yapıldığında aynı oturumda buraya yazılır.

---

Yeni runbook eklerken bu tabloyu güncelle.

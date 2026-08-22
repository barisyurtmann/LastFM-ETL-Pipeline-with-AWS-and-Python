# 21 — AWS kimlik bilgileri, `~/.aws` dosyaları ve credential chain

> **Kısa cevap** — AWS "sen kimsin?" sorusunu nasıl cevaplıyoruz?
>
> 1. **Access key çifti** (ID + secret) = makinenin kullanıcı adı + parolası. **Kimlik**
>    verir, **yetki vermez** — yetki, o kimliğe bağlı IAM policy'den gelir.
> 2. İki dosya, bilinçli olarak ayrı: `~/.aws/credentials` **sır**, `~/.aws/config` **ayar**.
> 3. **Credential chain**: `boto3` ve CLI kimlik bilgisini sıralı bir listede arar, ilk
>    bulduğunu kullanır. Zincirin **son** basamağı Lambda rolüdür — bu yüzden kod AWS'ye
>    taşınırken **tek satır değişmez**.

---

## 1. Neden

Kimlik doğrulamanın nerede durduğunu bilmiyorsan iki hatadan birini yaparsın:
anahtarı koda gömersin (sızıntı), ya da her ortam için kodu değiştirirsin (taşınamaz kod).
Bu notun tamamı bu iki hatayı önlemek için var.

---

## 2. IAM kavram haritası

> **IAM** = Identity and Access Management. AWS'nin "kim, neye, ne yapabilir" servisi.

| Terim | Tanım | Bizdeki karşılığı |
|---|---|---|
| **Principal** | İstek yapan kimlik | `lastfm-etl-dev` kullanıcısı |
| **IAM user** | **Kalıcı** kimlik. İnsan veya eski usul makine için | `lastfm-etl-dev` |
| **IAM role** | **Geçici** kimlik. Üstlenilir, saatlik yenilenen token verir | P3.4'te Lambda rolleri |
| **Policy** | Yetki belgesi (JSON). "Şu kaynakta şu eylemlere izin var" | `AdministratorAccess` |
| **ARN** | Amazon Resource Name — her kaynağın küresel kimliği | `arn:aws:iam::123...:user/lastfm-etl-dev` |
| **STS** | Security Token Service — kimlik/geçici token servisi | `aws sts get-caller-identity` |

ARN yapısı: `arn:aws:<servis>:<bölge>:<hesap-no>:<kaynak>`. IAM küresel bir servis
olduğundan bölge alanı **boş** kalır — `arn:aws:iam::123456789012:user/...` içindeki çift
iki nokta bu yüzden.

**Kimlik ≠ yetki.** Access key "ben `lastfm-etl-dev`'im" der. Ne yapabileceğini o kullanıcıya
bağlı policy söyler. Anahtarı değiştirmek yetkiyi değiştirmez; policy'yi değiştirmek anahtarı
etkilemez. İkisi bağımsız kadranlar.

---

## 3. Access key anatomisi

| Parça | Görünüm | Gizli mi | Kaybolursa |
|---|---|---|---|
| Access key ID | `AKIA` + 16 karakter | Hayır (log'da görünmesi normal) | IAM'de yazıyor |
| Secret access key | 40 karakter | **Evet** | **Kurtarılamaz** — yenisini üret |

**Kurallar ve sebepleri:**

| Kural | Sebep |
|---|---|
| **Root hesap için asla üretme** | Root'un yetkisi kısıtlanamaz. Sızarsa hesap tamamen kaybedilir |
| Kullanıcı başına **en fazla 2** anahtar | AWS bu limiti **rotation** için koydu: yenisini üret → geçir → eskisini sil |
| Her anahtara **description tag** | Tag'siz iki anahtar arasında hangisinin ölü olduğunu bilemezsin → silemezsin → bilinmeyen aktif anahtar kalır |
| Makine başına ayrı anahtar (2'ye kadar) | **Blast radius**: laptop çalınırsa sadece o anahtarı iptal edersin. **Attribution**: CloudTrail'de hangi makine olduğu görünür |
| Kullanılmayanı sil | "Last used" boş/eski anahtar, fark edilmeden kullanılabilecek anahtardır |

> **CloudTrail** = AWS'deki her API çağrısını kaydeden denetim servisi.
> **Blast radius** = bir sızıntının etki alanı.
> **Rotation** = sırrı, sızmadan önce planlı olarak yenisiyle değiştirme.

3+ makine gerekiyorsa doğru cevap 3. anahtar değil, **IAM Identity Center (SSO)**'dur:
`aws sso login` ile tarayıcıdan giriş yapılır, 8–12 saat geçerli **geçici** kimlik alınır,
diskte kalıcı sır durmaz. Kurumsal ortamların varsayılanı budur.

---

## 4. İki dosya — ve neden ayrı

`aws configure` dört soru sorar, **iki** dosya yazar:

```
~/.aws/credentials          ~/.aws/config
[default]                   [default]
aws_access_key_id=AKIA...   region = eu-central-1
aws_secret_access_key=...   output = json
```

> `~` = kullanıcı ana klasörü. Windows'ta `C:\Users\<kullanıcı>`. Git Bash `~`'ı anlar.

| Dosya | İçerik | Yedeklenir/paylaşılır mı |
|---|---|---|
| `credentials` | Sır | **Asla** |
| `config` | Ayar (bölge, çıktı formatı, profil tanımları) | Rahatça — dotfiles reposuna bile girer |

**Ayrımın sebebi** `.env` ↔ `pyproject.toml` ayrımıyla aynı: **sır ile ayar aynı dosyada
durmaz.** Tek dosya olsaydı ayarlar da sır muamelesi görürdü ve bölge ayarını bir ekip
arkadaşına gönderemezdin.

**Profile** = aynı makinede birden fazla AWS hesabı tutmanın yolu. Varsayılan `[default]`.
İkinci hesap: `aws configure --profile prod`, kullanımı `AWS_PROFILE=prod aws s3 ls` ya da
`boto3.Session(profile_name="prod")`.

**Bu iki dosya CLI'a ait değil, makineye aittir.** `boto3` de, CLI de, Terraform da,
VS Code AWS eklentisi de aynı dosyaları okur. `aws configure` çalıştırmamızın tek sebebi
buydu — CLI'ı öğrenmek için değil, bu dosyaları doğru formatta yazdırmak için.

---

## 5. Credential chain — notun kalbi

`boto3` ve CLI kimlik bilgisini **sıralı** arar. İlk bulduğu kazanır, gerisine bakmaz:

| # | Kaynak | Nasıl görünür | Bizde ne zaman |
|---|---|---|---|
| 1 | Kodda açık parametre | `boto3.client("s3", aws_access_key_id=...)` | **Asla** |
| 2 | Ortam değişkeni | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | CI/CD'de yaygın; bizde yok |
| 3 | `~/.aws/credentials` | `[default]` bloğu | **Şu an burası** (P1.2) |
| 4 | `~/.aws/config` | `credential_process`, SSO ayarları | Yok |
| 5 | **Container / EC2 / Lambda metadata servisi** | Görünmez — rol otomatik | **P3'te burası** |

**Bu tablo neden önemli:** P2.2'de `boto3.client("s3")` yazacağız. Laptopta 3. basamak
devreye girer. Aynı kod Lambda'ya taşındığında 1–4 boş olur, 5 devreye girer ve Lambda
kendi rolünün **geçici** kimliğini kullanır.

**Kod değişmez.** Kimlik bilgisini kendimiz okusaydık (`os.environ["AWS_SECRET..."]`),
Lambda'da o değişken olmadığı için patlardık ve kodu iki ortam için ikiye ayırmak zorunda
kalırdık. Zincir bu ayrımı gereksiz kılıyor.

Aynı sebeple `LASTFM_API_KEY` `.env`'de ama **AWS anahtarı `.env`'e girmez**: birini biz
okuyoruz, diğerini `boto3` kendi buluyor.

### Zincirin ısırdığı yer

Öncelik sırası hem çözüm hem tuzak. Ortam değişkeni (2) dosyayı (3) **yener**. Bir kere
`export AWS_ACCESS_KEY_ID=...` yaptıysan, `~/.aws/credentials`'ı düzeltmen o terminalde
hiçbir şeyi değiştirmez. Belirti: "dosyayı düzelttim ama hâlâ eski/yanlış kimlikle gidiyor."

Tanı komutu: `aws configure list` — her değerin **hangi kaynaktan** geldiğini yazar.
`cat ~/.aws/credentials` bu soruyu cevaplayamaz, çünkü dosyayı okumak zincirin kimi
kazandığını söylemez.

Aynı davranışı `python-dotenv`'in `override=False`'unda da ölçmüştük (P1.1, kontrol 2):
**gerçek ortam değişkeni dosyayı yener.** Aynı prensip, iki farklı araç.

---

## 6. Güvenlik: yapılmayacaklar listesi

| Yapma | Sebep |
|---|---|
| `aws configure set aws_secret_access_key AKIA...` | Sır **komutun kendisidir** → shell geçmişine (`~/.bash_history`) kalıcı yazılır. `aws configure`'ın soru-cevap biçimi `stdin` okur, geçmişe düşmez |
| `export AWS_SECRET_ACCESS_KEY=...` elle | Aynı sebep — geçmişe düşer |
| İndirilen `.csv`'yi saklamak | Görevi `aws configure`'a kadar. Sonrası `Downloads/`'ta duran açık sır |
| `~/.aws/`'ı OneDrive/Dropbox kapsamına almak | Sır makineden çıkar, nereye gittiğini bilemezsin |
| Ekran paylaşırken `cat ~/.aws/credentials` | Açıklama gerekmez |
| Anahtarı repoya koymak | GitHub'a `AKIA...` push edildiğinde bot'ların dakikalar içinde bulup kripto madenciliği başlattığı, belgelenmiş ve sık bir olay |

Linux/macOS'ta `aws configure` dosyayı `600` izniyle yazar (yalnız sahibi okur). Windows'ta
NTFS kullanıcı klasörü diğer kullanıcılara kapalıdır ama **yönetici okuyabilir**.

---

## 7. Kanıt

```bash
aws configure list
```

Her ayarın değerini ve **kaynağını** basar; secret'ı `****************ABCD` diye maskeler.
`Type` sütununda `shared-credentials-file` görürsen zincirin 3. basamağı kazanmış demektir.

```bash
aws sts get-caller-identity
```

Asıl kanıt: ağ üzerinden gerçek doğrulama yapar, dosya okumakla yetinmez.

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/lastfm-etl-dev"
}
```

Kontrol: `Arn` **`user/lastfm-etl-dev`** ile bitmeli. `root` yazıyorsa yanlış hesabın
anahtarı girilmiştir, devam edilmez.

---

## 8. Yanlış anlaşılan noktalar

| Barış önce şöyle sandı | Aslında |
|---|---|
| "Tek anahtar her makinede kullanılamaz, her PC'de yeni açmak gerek" | Teknik olarak tek anahtar her yerde çalışır. Ayırmak bir **tercih** — blast radius, attribution ve rotation kolaylığı için. Yayınlanmış bir zorunluluk değil |
| "Description tag kozmetik" | Tag yoksa ölü anahtar tespit edilemez, silinemez, aktif kalır. Güvenlik açığının adı budur |
| "Access key yetki verir" | Kimlik verir. Yetki policy'den gelir. İkisi bağımsız |
| "AWS anahtarı da `.env`'e konur, diğer sırlar gibi" | Hayır. `.env` **projenin** sözleşmesi; AWS kimliği **makinenin** kimliği. Ayrıca `.env`'e koysak kodun onu okuması gerekirdi ve Lambda'da zincir kırılırdı |
| "Lambda'ya da anahtar koyacağız" | Hayır. Lambda **rol** kullanır: geçici, otomatik yenilenen kimlik. Kalıcı sır yok. P3.4 |
| "`~/.aws/` AWS CLI'ın klasörü" | Makinenin klasörü. `boto3`, Terraform, IDE eklentileri — hepsi aynı yerden okur |

---

## 9. Komut özeti

| Komut | Ne yapar |
|---|---|
| `aws configure` | Dört soru sorar, iki dosyayı yazar |
| `aws configure list` | Değerlerin **kaynağını** gösterir (secret maskeli) |
| `aws configure --profile X` | Yeni bir profil ekler |
| `aws sts get-caller-identity` | "Ben kimim?" — ağ üzerinden doğrular |
| `aws sts get-caller-identity --profile X` | Belirli profille aynısı |

---

## 10. Bir sonraki turda (bu projede yok)

- IAM Identity Center (SSO) ile geçici kimlik
- `AssumeRole` ve `~/.aws/config` içinde `role_arn` + `source_profile` zinciri
- MFA gerektiren policy koşulu (`aws:MultiFactorAuthPresent`)
- AWS Secrets Manager / SSM Parameter Store — uygulama sırlarını AWS'de tutmak
- `gitleaks` / `detect-secrets` pre-commit hook'u — `AKIA` desenini commit anında yakalamak

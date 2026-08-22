# 03 — AWS hesabı, kimlik ve CLI kurulumu

**Son doğrulama:** 2026-08-22 (iş makinesi, Windows + Git Bash) · **Süre:** ~45 dk
**Sıklık:** Bölüm 1–5 hesap başına **bir kez** · Bölüm 6–9 **her yeni makinede**
**Kapsam:** ROADMAP adım **P1.2**

**Bitiş durumu:**

- AWS hesabı var, root kullanıcı MFA ile kilitli ve günlük işte kullanılmıyor
- Aylık 5 USD eşiğinde budget alarmı kurulu
- `lastfm-etl-dev` IAM kullanıcısı var, MFA'lı, konsola onunla giriliyor
- `aws sts get-caller-identity` çalışıyor ve `Arn` `user/lastfm-etl-dev` ile bitiyor
- Secret access key diskte yalnızca `~/.aws/credentials` içinde duruyor

> **UI uyarısı:** AWS konsolu sık değişir. Buton adı tutmuyorsa adımın **amacına** bak;
> kavram aynı kalır, etiket değişir. Kavramların açıklaması için →
> [`notes/21`](../notes/21-aws-credentials-and-the-credential-chain.md)

---

## Ön koşullar

| Gerekli | Not |
|---|---|
| E-posta adresi | Hesabın kimliği. Sonradan değiştirmek zahmetli |
| Kredi kartı | Free tier'da bile zorunlu. Doğrulama için ~1 USD çekilip iade edilir |
| Telefon | SMS doğrulama |
| **Authenticator uygulaması** | Google Authenticator, Microsoft Authenticator, Authy, 1Password vb. Telefonda kurulu olsun |
| Git Bash (Windows) | Komutlar bash sözdizimiyle yazıldı |

---

## Bölüm 1 — AWS hesabı aç

> Yalnızca hesap yoksa. Varsa Bölüm 6'ya atla.

1. https://portal.aws.amazon.com/billing/signup → e-posta + hesap adı
2. E-postaya gelen doğrulama kodunu gir
3. Root kullanıcı parolasını belirle — **parola yöneticisine kaydet**, bir daha nadiren gireceksin
4. Hesap türü: **Personal**
5. Kredi kartı, adres, telefon doğrulama
6. Destek planı: **Basic support — Free**

**Doğrulama:** https://console.aws.amazon.com/ adresine root e-postasıyla girebiliyorsun.

---

## Bölüm 2 — Root kullanıcıyı kilitle (MFA)

> **Root** = hesabı açan asıl kullanıcı. Yetkisi **kısıtlanamaz**, faturayı kapatabilir,
> hesabı silebilir. Root sızarsa kurtarma yolu yoktur. Bu yüzden ilk iş onu kilitlemek.
> **MFA** = Multi-Factor Authentication — parolaya ek olarak, telefondaki uygulamanın
> ürettiği 30 saniyelik kod.

1. Konsolda sağ üstteki **hesap adı** menüsü → **Security credentials**
2. **Multi-factor authentication (MFA)** bölümü → **Assign MFA device**
3. **Device name**: `root-telefon` gibi tanınır bir ad
4. Tür: **Authenticator app** → **Next**
5. **Show QR code** → telefondaki authenticator uygulamasıyla tara
6. **MFA code 1**: uygulamadaki kodu yaz → ~30 sn bekle → **MFA code 2**: **yeni** kodu yaz
7. **Add MFA**

> **Junior tuzağı:** İki kutuya aynı kodu yazmak. AWS **ardışık iki farklı** kod ister —
> saatin doğru senkronize olduğunu kanıtlamak için. Bekle, yeni kodu yaz.

**Kurtarma kodu:** Telefonu kaybedersen root'a giremezsin. Authenticator uygulamasının
yedeği (bulut senkronu) açık olsun, ya da QR ekranındaki **secret key**'i parola
yöneticisine kaydet.

**Doğrulama:** Çıkış yap, tekrar gir → parola sonrası MFA kodu soruluyor.

**Bundan sonra root ile giriş yapılmaz.** Root sadece şunlar için: hesap kapatma, fatura
bilgisi değiştirme, destek planı, bazı hesap seviyesi ayarlar.

---

## Bölüm 3 — Budget alarm (harcamadan **önce**)

> Sıra önemli: korkuluk, uçurumdan **önce** kurulur. Öğrenirken yanlış bir ayar (açık
> kalan bir Crawler, döngüye giren bir Lambda) sessizce fatura üretir. Alarm olmadan
> bunu ay sonunda öğrenirsin.

1. https://console.aws.amazon.com/cost-management/ → sol menüde **Budgets**
2. **Create budget**
3. **Budget setup** → **Use a template (simplified)**
4. **Templates** → **Monthly cost budget**
5. **Budgeted amount**: `5` (USD)
6. **Email recipients**: kendi e-postan
7. **Create budget**

> Alternatif şablon: **Zero spend budget** — free tier'ı aşan **ilk** kuruşta uyarır.
> Daha agresif; öğrenirken bunu da eklemek meşru.

**Bu bir alarm, bir limit değildir.** AWS harcamayı durdurmaz, sadece e-posta atar.
Sert limit isteyen bir mekanizma AWS'de yoktur — bilinçli bir tasarım (prod'da servisin
aniden durması genelde daha kötüdür).

**Doğrulama:** Budgets listesinde bütçe görünüyor. Bildirim e-postası maliyet verisi
oluştukça (24 saate kadar gecikmeli) tetiklenir.

---

## Bölüm 4 — IAM kullanıcı oluştur

> Root ile günlük iş yapılmaz. Günlük iş için **IAM user** açılır.

1. Konsol araması → **IAM** → sol menü **Users** → **Create user**
2. **User name**: `lastfm-etl-dev`
3. **Provide user access to the AWS Management Console** → **işaretle** (konsoldan
   çalışacağız)
4. **I want to create an IAM user** seçeneğini seç
5. Parola: **Custom password** → parola yöneticisine kaydet.
   **User must create a new password at next sign-in** → kendi hesabınsa işareti kaldır
6. **Next** → **Permissions options** → **Attach policies directly**
7. Listede **`AdministratorAccess`** → işaretle
8. **Next** → **Create user**
9. Açılan ekrandaki **console sign-in URL**'ini kaydet:
   `https://<hesap-no>.signin.aws.amazon.com/console`

> **Neden `AdministratorAccess`?** Least privilege ilkesi **makine kimliklerine** uygulanacak
> (Lambda rolleri, P3.4). Tek kişilik öğrenme hesabında insanı kısmak her adımda
> `AccessDenied` demektir. Bu bir mühendislik tercihi, yayınlanmış bir standart değil.
> Ekip ortamında insan kullanıcı da kısılır.

**Doğrulama:** Gizli/incognito pencerede sign-in URL'i ile `lastfm-etl-dev` olarak giriş
yapılabiliyor.

---

## Bölüm 5 — IAM kullanıcıya MFA

Bu kullanıcı `AdministratorAccess` taşıyor — yani root kadar olmasa da tehlikeli.

1. **IAM** → **Users** → `lastfm-etl-dev`
2. **Security credentials** sekmesi → **Multi-factor authentication (MFA)** →
   **Assign MFA device**
3. **Device name**: `lastfm-etl-dev-telefon`
4. **Authenticator app** → **Next**
5. **Show QR code** → tara → **MFA code 1** ve **MFA code 2** (ardışık iki farklı kod)
6. **Add MFA**

**Doğrulama:** Çıkış → sign-in URL ile giriş → MFA soruluyor.

---

## Bölüm 6 — Access key üret

> **Bu bölüm her yeni makinede tekrarlanır.** Kullanıcı başına en fazla **2** anahtar
> vardır. Kavramlar → [`notes/21`](../notes/21-aws-credentials-and-the-credential-chain.md)

> **Sıra tavsiyesi:** Bölüm 7'yi (CLI kurulumu) **önce** yap. Secret yalnızca üretildiği
> ekranda görünür; CLI hazırsa secret ekrandan doğrudan `aws configure`'a gider ve
> hiç beklemez.

1. **IAM** → **Users** → `lastfm-etl-dev` → **Security credentials**
2. **Access keys** bölümü. **Kullanılmayan eski anahtar varsa:** üç nokta →
   **Deactivate** → sonra **Delete**
3. **Create access key**
4. Use case: **Command line interface (CLI)** → alttaki onay kutusunu işaretle → **Next**
5. **Description tag value**: makineyi tanımlayan bir ad — `cli-otomasyon-laptop`,
   `cli-ev-laptop`
6. **Create access key**
7. **Download .csv file** — ya da iki değeri kopyala. **Bölüm 8 bitene kadar sayfayı kapatma**

> **Secret access key yalnızca bu ekranda görünür.** Kaybedilirse kurtarılamaz: eskisini
> sil, yenisini üret. Ücretsiz, panik yok.

> **Description tag'i atlama.** Tag'siz iki anahtardan hangisinin ölü olduğunu bilemezsin,
> bilemediğin için silemezsin, silmediğin için bilinmeyen bir aktif anahtar kalır.

**Doğrulama:** IAM'de anahtar `Active`, tag görünüyor, "Last used" boş.

---

## Bölüm 7 — AWS CLI kur

**Windows (Git Bash):**

```bash
winget install --id Amazon.AWSCLI -e
```

| Bayrak | Ne yapar |
|---|---|
| `--id` | Paketi görünen adıyla değil benzersiz kimliğiyle seç |
| `-e` | `--exact` — kısmi eşleşmeleri getirme |

**Kurulumdan sonra terminali kapat ve yeniden aç.** Kurulum `PATH` değişkenini günceller;
açık duran terminal `PATH`'i başlarken bir kez okumuştur, eski listeyi taşır.

**macOS:** `brew install awscli` · **Linux:** AWS'nin resmî `awscli-exe-linux-x86_64.zip`
paketi. `pip install awscli` **kullanma** — o eski v1'i kurar.

**Doğrulama:**

```bash
aws --version
```

Çıktı `aws-cli/2.` ile başlamalı.

---

## Bölüm 8 — `aws configure`

```bash
aws configure
```

| Soru | Değer |
|---|---|
| `AWS Access Key ID` | Bölüm 6'daki `AKIA...` |
| `AWS Secret Access Key` | Bölüm 6'daki 40 karakter |
| `Default region name` | `eu-central-1` |
| `Default output format` | `json` |

Değerleri **yapıştır**, elle yazma.

> **Asla `aws configure set aws_secret_access_key <değer>` biçimini kullanma** — orada sır
> komutun kendisidir ve shell geçmişine kalıcı yazılır. Soru-cevap biçimi `stdin` okur,
> geçmişe düşmez.

Bu komut iki dosya yazar:

| Dosya | İçerik |
|---|---|
| `~/.aws/credentials` | Access key ID + secret |
| `~/.aws/config` | `region`, `output` |

**Bölge kritik:** Bucket'ın bölgesi sonradan **değişmez**. `eu-central-1` (Frankfurt)
seçildi — İstanbul'a en yakın, Lambda/Glue/Athena hepsi mevcut.

---

## Bölüm 9 — Doğrulama

```bash
aws --version
aws configure list
aws sts get-caller-identity
```

Beklenen:

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/lastfm-etl-dev"
}
```

| Kontrol | Beklenen |
|---|---|
| `aws --version` | `aws-cli/2.` ile başlıyor |
| `aws configure list` | `region` = `eu-central-1`, secret maskeli, `Type` = `shared-credentials-file` |
| `Arn` | **`user/lastfm-etl-dev`** ile bitiyor — `root` **değil** |
| `ls ~/.aws/` | `config` ve `credentials` |

`Arn`'de `root` görürsen **dur** — yanlış hesabın anahtarı girilmiş.

---

## Bölüm 10 — Temizlik

```bash
rm ~/Downloads/*accessKeys.csv    # dosya adını kontrol ederek
```

CSV'nin görevi Bölüm 8 ile bitti. `Downloads/` klasöründe duran secret, `.env`'i
commit'lemekle aynı sınıf bir hatadır.

Ayrıca: `~/.aws/` klasörünün OneDrive/Dropbox senkronizasyon kapsamında **olmadığını**
doğrula. Windows'ta `~/.aws` doğrudan `C:\Users\<kullanıcı>\` altındadır; Masaüstü veya
Belgeler senkronize ediliyorsa etkilenmez.

---

## Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `aws: command not found` | Kurulum `PATH`'i güncelledi, terminal eski `PATH`'i taşıyor | Terminali kapat-aç. Kurulumu tekrarlama |
| `aws-cli/1.x` | `pip install awscli` ile v1 kurulmuş | v1'i kaldır, `winget`/`brew` ile v2 kur |
| `InvalidClientTokenId` | Access key ID yanlış veya silinmiş | Bölüm 6'yı tekrarla |
| `SignatureDoesNotMatch` | Secret yanlış yapıştırılmış (baş/son boşluk) **veya sistem saati kaymış** | `aws configure`'ı tekrar çalıştır; düzelmezse saati senkronize et. İmza zaman damgası taşır, 5 dk'dan fazla sapma reddedilir |
| `Unable to locate credentials` | `~/.aws/credentials` yok | Bölüm 8 |
| Dosyayı düzelttim ama hâlâ eski kimlik | Ortam değişkeni dosyayı **yeniyor** (credential chain 2 > 3) | `aws configure list` ile kaynağı gör; `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY` |
| `AccessDenied` | Policy eksik | IAM'de `AdministratorAccess` bağlı mı |
| MFA kodu kabul edilmiyor | İki kutuya aynı kod yazıldı, veya telefon saati kaymış | Ardışık **iki farklı** kod. Telefonda otomatik saat açık olsun |

---

## Geri alma

| Durum | Ne yapılır |
|---|---|
| Secret kaybedildi | IAM → anahtarı **Deactivate** → **Delete** → yeni anahtar üret (Bölüm 6). Ücretsiz |
| Yanlış bölge girildi | `aws configure` tekrar çalıştır, sadece region'ı değiştir. **Ama oluşturulmuş bucket'ın bölgesi değişmez** — yeni bucket açıp veriyi taşımak gerekir |
| Anahtar sızdı (repoya girdi, paylaşıldı) | **Önce Deactivate, sonra Delete.** Sonra CloudTrail'den o anahtarla yapılan çağrılara bak. Repodan silmek yetmez — git geçmişinde kalır, anahtar iptal edilmeden güvenli değildir |
| Makine elden çıkıyor | O makinenin tag'li anahtarını IAM'den sil |
| Hesabı tamamen kapatma | Root ile giriş → Account → Close account. Bucket'lar önce boşaltılmalı |

---

## Yeni makine kısa yolu

Hesap zaten kuruluysa, yeni bir bilgisayarda yapılacaklar:

1. **Bölüm 6** — yeni access key (tag: o makinenin adı). 2 anahtar limiti doluysa
   kullanılmayanı sil
2. **Bölüm 7** — AWS CLI kur
3. **Bölüm 8** — `aws configure`
4. **Bölüm 9** — doğrula
5. **Bölüm 10** — CSV'yi sil

Ayrıca repo tarafı için: `git clone`, `uv sync`, `.env` oluşturma →
[`00 — Yeni makinede projeyi çalışır hale getirme`](00-new-machine-setup.md).

---

## Kaynaklar

- [Create an IAM user in your AWS account](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- [Assign a virtual MFA device in the AWS Management Console](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa_enable_virtual.html)
- [Using a budget template (simplified)](https://docs.aws.amazon.com/cost-management/latest/userguide/budget-templates.html)
- [Creating a cost budget](https://docs.aws.amazon.com/cost-management/latest/userguide/create-cost-budget.html)

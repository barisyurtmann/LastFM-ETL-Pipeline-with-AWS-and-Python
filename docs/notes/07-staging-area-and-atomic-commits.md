# 07 — Staging area ve atomik commit

> Adım 0.4 · 2026-08-10

Not 02 commit **mesajını** anlatıyor. Bu not commit'in **kapsamını** anlatıyor:
diskte beş dosya değiştiyse, bunlardan sadece ikisini nasıl commit'lersin ve neden?

> **Kısa cevap** — Diskte beş dosya değiştiyse commit'in kapsamını nasıl seçersin?
>
> 1. `git commit` diskin değil index'in fotoğrafını çeker; `git diff` disk↔index, `git diff --staged` index↔HEAD gösterir.
> 2. `git add` içeriği o anda dondurur: add sonrası düzenleme commit'e girmez, `git status` dosyayı hem staged hem unstaged listeler.
> 3. `git commit -am` untracked dosyaları almaz; commit mesajını "ve" olmadan yazamıyorsan iki commit olmalıydı.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

## Git'in üç bölgesi

```
working tree  ──git add──>  index (staging area)  ──git commit──>  repository
   disk                        ".git/index"                        (HEAD, geçmiş)
```

| Bölge | Nedir | Soruyu cevaplar |
|---|---|---|
| Working tree | Diskteki gerçek dosyalar. Editörün yazdığı yer | "Şu an dosyada ne var?" |
| Index (staging area) | Bir sonraki commit'in **taslağı** | "Commit'e ne girecek?" |
| Repository | Commit edilmiş geçmiş | "Geçmişte ne oldu?" |

`git commit` diskin fotoğrafını çekmez — **index'in** fotoğrafını çeker. Aradaki bu
ayrım Git'i çoğu VCS'ten ayıran şeydir ve `git add` alışkanlığının tüm sebebi budur.

## Neden ara bir bölge var

Çünkü **çalışma ritmin ile geçmişin okunabilirliği aynı şey değildir.**

Gerçekte tek oturumda birbiriyle ilgisiz üç şey yaparsın: bir bug düzeltirsin, bir not
yazarsın, bir de gözüne çarpan yazım hatasını düzeltirsin. Diskte hepsi karışık durur.
Index sana şunu söyler: *"karışık çalış, düzenli commit'le."*

Ara bölge olmasaydı iki seçeneğin olurdu: ya her şeyi tek commit'e tıkarsın (geçmiş
okunamaz, `git bisect` işe yaramaz, tek dosyayı geri almak imkânsız), ya da bir işi
bitirmeden diğerine hiç dokunmazsın (gerçekçi değil).

## İki commit nasıl atılır

Diskte iki ilgisiz değişiklik var. Sıra şu — **her commit'ten önce `git status`**:

```bash
git status                    # ikisi de "modified" gorunur

git add .gitignore
git status                    # .gitignore staged, digeri degil
git commit -m "fix: ..."      # SADECE .gitignore commit'lendi

git add docs/
git status
git commit -m "docs: ..."     # ikinci commit
```

İlk `commit`'ten sonra index boşalır. İkinci `git add` sıfırdan başlar — birinci
commit'in dosyası ikinciye **karışmaz**. Sıralama önemli değil, ayrım önemli.

`git add docs/` bir klasör alır: altındaki tüm değişiklikler (yeni + değiştirilmiş)
staged olur. Tek tek yazmak da olur, sonuç aynı.

## "Başkasının yazdığı dosya" diye bir şey yok

Bir dosyayı kim yazdı — sen mi, editör mü, bir script mi, bir asistan mı — Git'i
hiç ilgilendirmez. Git yalnızca **diskte ne var** sorusuna bakar. Dosya diskteyse
`git status` onu görür, `git add` ile stage'lenir. Ekstra bir işlem yoktur.

Bunu içselleştirmenin pratik faydası: `git status` **tek otoritedir.** "Şu dosya
eklendi mi acaba?" sorusunun cevabı hafızanda değil, `git status` çıktısında.

## `git diff` vs `git diff --staged` — en çok karıştırılan iki komut

İki bölge sınırı var, dolayısıyla iki farklı diff:

| Komut | Neyi neyle karşılaştırır | Cevapladığı soru |
|---|---|---|
| `git diff` | working tree ↔ index | "Henüz stage'lemediğim ne var?" |
| `git diff --staged` | index ↔ HEAD | **"Bu commit'te tam olarak ne gidecek?"** |
| `git diff HEAD` | working tree ↔ HEAD | "Son commit'ten beri toplamda ne değişti?" |

**Refleks haline gelmesi gereken:** `git add`'den sonra, `git commit`'ten önce
`git diff --staged`. Commit'lediğin şeyi görmenin tek yolu bu — `git diff` o noktada
boş döner ve bu "değişiklik yok" demek **değildir**, "stage'lenmemiş değişiklik yok"
demektir.

### Diff çıktısı nasıl okunur

Format **unified diff** — Git'e özel değil, POSIX `diff -u` formatı. Aynı formatı
`git show`, `git log -p`, GitHub PR ekranı ve `patch` komutu da kullanır. Bir kez
öğrenilir, her yerde işe yarar.

0.4'te düzeltilen `.gitignore`'ın gerçek çıktısı:

```diff
diff --git a/.gitignore b/.gitignore
index 6643e9d..086acf6 100644
--- a/.gitignore
+++ b/.gitignore
@@ -1,10 +1,14 @@
 # --- Python build artifacts ---
-__pycache__/          # compiled bytecode, regenerated on every run
+# compiled bytecode, regenerated on every run
+__pycache__/
 
 # --- Virtual environment ---
```

Satır satır:

| Satır | Anlamı |
|---|---|
| `diff --git a/... b/...` | Başlık. `a/` = **eski** hâl, `b/` = **yeni** hâl |
| `index 6643e9d..086acf6 100644` | Eski ve yeni içeriğin blob hash'leri. `100644` = normal dosya (`100755` çalıştırılabilir, `120000` symlink) |
| `--- a/.gitignore` | Eski sürüm işareti |
| `+++ b/.gitignore` | Yeni sürüm işareti |
| `@@ -1,10 +1,14 @@` | **Hunk başlığı** — aşağıda |
| ` ` (boşlukla başlayan) | Değişmemiş bağlam satırı |
| `-` | Silinen satır |
| `+` | Eklenen satır |

**Hunk başlığı `@@ -1,10 +1,14 @@` şöyle okunur:**

```
@@ -1,10  +1,14 @@
    │ │     │ │
    │ │     │ └── yeni dosyada 14 satır
    │ │     └──── yeni dosyada 1. satırdan başlıyor
    │ └────────── eski dosyada 10 satır
    └──────────── eski dosyada 1. satırdan başlıyor
```

`-` eski, `+` yeni. Yani bu blok, dosyanın 1–10. satırlarının yerine 1–14. satırların
geçtiğini söylüyor. Büyük dosyalarda birden fazla hunk olur; her `@@` yeni bir bölge.

**Kritik nokta: Git satır "değiştirme" diye bir şey bilmez.** Bir satırı düzenlersen
diff bunu `-eski` + `+yeni` olarak gösterir. Bu yüzden düzenlenmiş bir satır ile
silinip başka yere yazılmış bir satır diff'te aynı görünür. Aynı sebeple `git log`
bir satırın "taşındığını" değil, silinip eklendiğini raporlar.

**Junior tuzağı:** `+`/`-` sayısına bakıp iş miktarı ölçmek. Not 03'teki
`1127 insertions / 1127 deletions` olayı bunun kanıtı — içerik hiç değişmemişti,
sadece satır sonları CRLF'e dönmüştü. Diff satır bazlıdır, anlam bazlı değil.

### Hangi diff varyantı ne zaman

| Komut | Ne gösterir |
|---|---|
| `git diff` | Stage'lenmemiş değişiklikler (disk ↔ index) |
| `git diff --staged` | Commit'lenecek olan (index ↔ HEAD). `--cached` aynı şey |
| `git diff HEAD` | Toplam (disk ↔ son commit) |
| `git diff --stat` | Satır satır değil, dosya başına özet — "kaç dosya, kaç satır" |
| `git diff --name-only` | Sadece dosya adları. Script'e beslemek için |
| `git diff <commit> <commit>` | İki commit arası |
| `git diff -w` | Boşluk farklarını yok say. Indentation değişikliğinde diff'i okunur kılar |
| `git show <commit>` | Tek bir commit'in diff'i (`git diff` değil ama aynı format) |

### `git status --short` çıktısı da aynı mantıkta

```
 M .gitignore        <- bosluk + M
M  .gitignore        <- M + bosluk
MM .gitignore        <- ikisi birden
?? yeni-dosya.md
```

**İki sütun var: birincisi index'in, ikincisi working tree'nin durumu.**

| Kod | Anlamı |
|---|---|
| `M ` | Index'te değişmiş — stage'li, commit'e hazır |
| ` M` | Diskte değişmiş, stage'lenmemiş |
| `MM` | Stage'lendi, sonra tekrar düzenlendi (aşağıdaki snapshot tuzağı) |
| `A ` | Yeni dosya, stage'li |
| `??` | Untracked — Git bu dosyayı hiç tanımıyor |
| `!!` | Ignore'lu (yalnızca `--ignored` ile görünür) |

Sütunun **hangisi** olduğuna bakmak, `git status`'ün uzun hâlindeki "Changes to be
committed" / "Changes not staged" ayrımını okumakla aynı şey — sadece iki karakterde.

## Snapshot tuzağı: `add` anı dondurur

`git add` dosyanın **o andaki içeriğini** index'e kopyalar. Sonra dosyayı tekrar
düzenlersen, yeni hali commit'e **girmez**:

```bash
git add rapor.md      # index'te: v1
# ... dosyayi duzenledin ...
git commit            # commit'lenen: v1. Diskte: v2.
```

`git status` bu durumu dürüstçe gösterir — aynı dosya hem "staged" hem "not staged"
listesinde görünür:

```
Changes to be committed:
        modified:   rapor.md
Changes not staged for commit:
        modified:   rapor.md
```

Bu satırı görürsen "garip" değil, "yarısı stage'li" demektir. Çözüm: `git add` tekrar.

## Geri alma

| Durum | Komut | Ne yapar |
|---|---|---|
| Yanlışlıkla stage'ledim | `git restore --staged <path>` | Index'ten çıkarır, **dosyaya dokunmaz** |
| Değişikliği tamamen atmak istiyorum | `git restore <path>` | Diski HEAD'e döndürür — **geri dönüşü yok** |
| Son commit'in mesajı/kapsamı yanlış | `git commit --amend` | Son commit'i yeniden yazar |

`git restore` (Git 2.23+) `git checkout`'un veri kaybettiren belirsizliğini çözmek için
geldi — eski rehberlerde `git checkout -- <path>` görürsün, aynı işi yapar ama aynı komut
branch de değiştirdiği için tehlikelidir. Yeni kodda `restore` kullan.

`--amend` **yalnızca push'lanmamış** commit'te güvenlidir. Push'landıysa geçmişi
değiştirmek force-push gerektirir ve repoyu klonlamış herkesi bozar.

## Kısmi commit: `git add -p`

Aynı **dosyada** iki ilgisiz değişiklik varsa, dosya bazında ayıramazsın:

```bash
git add -p <path>
```

Değişikliği hunk hunk gezer, her biri için sorar: `y` (stage'le), `n` (atla),
`s` (daha küçük parçalara böl), `q` (çık).

Bu bir titizlik gösterisi değil — geçmişin `git revert` ve `git bisect` ile
kullanılabilir kalmasının bedeli. Bir commit iki işi birden yapıyorsa, birini geri
almak için diğerini de geri almak zorunda kalırsın.

## Junior tuzakları

| Tuzak | Neden kötü |
|---|---|
| `git add .` refleksi | Ne eklediğini görmeden commit'lersin. `.env`'in repoya girdiği senaryoların çoğu böyle başlar |
| `git commit -am "..."` | `-a` **untracked** dosyaları almaz — "hepsini ekledim" sanırsın, yeni dosya dışarıda kalır. Ayrıca kapsamı hiç düşünmemiş olursun |
| `git diff` boş diye "değişiklik yok" sanmak | Stage'lenmiş olabilir. `git diff --staged`'e bak |
| Gün sonunda tek dev commit | "Bugün ne yaptım" bir commit değil. Commit **iş birimi**dir, **zaman birimi** değil |

## Commit ne zaman atılır — pratik kural

**Geri dönmek isteyeceğin her noktada.** Commit'in maliyeti sıfır; geri dönecek nokta
olmamasının maliyeti bir günlük iş.

Ölçüt: commit mesajını `ve` kullanmadan yazabiliyor musun?
`fix: correct gitignore patterns **and** update notes` → iki commit olmalıydı.

## Mülakat

*"Staging area ne işe yarar?"* → **"Commit'in kapsamını, çalışma ritmimden bağımsız
seçmemi sağlar. Diskte karışık çalışırım, geçmişe atomik commit'ler bırakırım.
Atomik commit de `revert` ve `bisect`'in çalışabilmesinin ön şartıdır."**

Devamı gelirse: `git diff --staged`'in ne zaman kullanıldığını sorarlar. Cevap:
her `git commit`'ten hemen önce.

# 02 — Commit mesajları ve ilk commit

> Adım 0.2 · 2026-08-07

> **Kısa cevap** — İlk commit'te ne olmalı ve commit mesajı hangi cümleyi tamamlamalı?
>
> 1. Root commit'in ebeveyni yok, `rebase --root` zahmetli — bu yüzden ilk commit sadece .gitignore olur.
> 2. Subject emir kipinde yazılır: "Bu commit uygulandığında repo şunu yapacak: ___" cümlesini tamamlamalı.
> 3. Subject "ne", body "neden" der; `chore: add .gitignore` body istemez, `fix: retry on 5xx only` ister.
>
> Bu üçü yeterliyse aşağısını okumana gerek yok.

## İlk commit'te ne olur

Cevap: **sadece `.gitignore`.** Gerekçesi iki tane, ve ikisi de "koruma" ile ilgili değil.

**1. Commit atomikliği.**
Bir commit **tek bir mantıksal değişiklik** olmalı. `.gitignore` eklemek bir iş, paket
iskeletini kurmak başka bir iş. Somut faydası: altı ay sonra `git log --oneline` ile
repo'nun hikâyesi okunabilir olur, ve `git bisect` ile hata ararken her commit'in tek bir
şeyi değiştirmesi işi kolaylaştırır.

**2. Root commit özeldir.**
Git geçmişindeki ilk commit'in ebeveyni yoktur, bu yüzden sonradan değiştirmek
(`git rebase --root`) diğerlerinden zahmetlidir. Küçük ve zararsız tutmak işe yarar.

**Alternatif ve trade-off:** bazı ekipler `git commit --allow-empty` ile tamamen boş bir
root commit atar, böylece her gerçek commit rebase edilebilir olur. Monorepo'larda ve
geçmişi sık yeniden yazan ekiplerde görülür. Küçük projede gereksiz karmaşıklık.

## Conventional Commits

Gerçek bir spesifikasyon — [conventionalcommits.org](https://www.conventionalcommits.org).
Angular ekibinden çıktı, yaygın kabul görüyor. Format:

```
<type>: <subject>
```

| Type | Ne zaman |
|---|---|
| `feat` | Yeni özellik |
| `fix` | Hata düzeltme |
| `chore` | Kod davranışını değiştirmeyen bakım işi |
| `docs` | Sadece dokümantasyon |
| `test` | Sadece test |
| `refactor` | Davranış aynı, yapı değişti |
| `build` | Bağımlılık, paketleme |
| `ci` | CI yapılandırması |

### Subject kuralları

- **Emir kipi** — `add`, `added` veya `adds` değil
- Küçük harfle başla
- Sonuna nokta koyma
- 50 karakteri geçme

**Emir kipinin gerekçesi:** git'in kendi ürettiği mesajlar da öyle (`Merge branch...`,
`Revert...`). Mesaj şu cümleyi tamamlamalı:

> *"Bu commit uygulandığında repo şunu yapacak: \_\_\_"*

`add .gitignore` tamamlıyor. `added .gitignore` tamamlamıyor.

### Gövde (body) ne zaman yazılır

Subject **ne** yaptığını söyler. Gövde **neden** yaptığını söyler — ve gövde ancak "neden"
apaçık değilse gerekir. `chore: add .gitignore` gövde istemez.
`fix: retry on 5xx only` ister: neden 4xx'te retry etmiyoruz?

## Junior tuzağı

`update`, `fix stuff`, `changes`, `wip`, `.` — altı ay sonra `git log`'a bakınca hiçbir
şey ifade etmezler. Portfolyo repoya bakan biri commit geçmişini **ilk** fark eder;
kod kalitesinden önce orayı okur.

## Commit atmadan önceki refleks

```bash
git add .gitignore
git status          # ← bunu atlama
git commit -m "chore: add .gitignore"
```

`git status`'ü atlamamak, sırları repoya sokan tek şeyi önleyen alışkanlıktır.
`git add .` yazıp ne eklediğine bakmadan commit'lemek, `.env`'in repoya girdiği
senaryoların çoğunun başlangıcıdır.

## Doğrulama

```bash
git log --oneline
git show --stat HEAD
```

Beklenen: tek commit, `1 file changed`.

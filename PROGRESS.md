# XYZ — ish jarayoni (PROGRESS)

Bu fayl loyihadagi UI va yangi funksiyalar bo‘yicha qilingan ishlarni doimiy yozib boradi.

## Maqsad

- Bosh sahifa: Asoschilar · O‘qituvchilar · Oy o‘quvchisi
- Reyting (faqat login)
- Admin CRUD (asoschilar + o‘qituvchi rasmlari)
- Profil / butun sayt dizayni + animatsiyalar
- Admin panel UI/UX (tushunarli o‘zbekcha interfeys)
- Asoschi / o‘qituvchi batafsil sahifa (bosilganda to‘liq ma’lumot)

## Holat (2026-07-25)

| # | Vazifa | Holat |
|---|--------|-------|
| 1 | Asoschi modeli + admin CRUD + rasm | ✅ |
| 2 | O‘qituvchi avatar (admin/profil) | ✅ |
| 3 | Reyting faqat login qilganlarga | ✅ |
| 4 | Oy o‘quvchisi reyting boshida (rasm bilan) | ✅ |
| 5 | Profil dizayni | ✅ |
| 6 | Sayt UI + yangi animatsiyalar | ✅ |
| 7 | Admin panel UI/UX (HTML/CSS) | ✅ |
| 8 | Asoschi/o‘qituvchi click → to‘liq ma’lumot | ✅ |
| 9 | To‘liq profil maydonlari admin orqali | ✅ |

## Holat (2026-07-27) — KAMCHILIKLAR (to‘lovsiz)

| # | Vazifa | Holat |
|---|--------|-------|
| 1 | Obuna: tarif/narx/CTA so‘rov (onlayn to‘lov YO‘Q) | ✅ |
| 2 | Obuna muddatini uzaytirish (eski muddat + kun) | ✅ |
| 3 | Video tomosha foizi → complete + test | ✅ |
| 4 | Imtihon timer/submit + davom ettirish | ✅ |
| 5 | Exam UI asosiy dizaynga moslash | ✅ |
| 6 | 404/403/500 brend | ✅ |
| 7 | Kabinet: fan/kurs progress + mini chart | ✅ |
| 8 | Dashboard → Kabinet, nav active, ?next= | ✅ |
| 9 | Parol tiklash + telefon validatsiya | ✅ |
| 10 | Profil: full_bio/education/achievements/telegram | ✅ |
| 11 | O‘qituvchi: kurs/modul/mavzu edit-delete + daraxt | ✅ |
| 12 | Freemium pin (`is_free_preview`) | ✅ |
| 13 | Fan/kurs rasmlari kartochkada | ✅ |
| 14 | Reytingda «Siz» belgisi | ✅ |
| 15 | Breadcrumb / empty states / mobil jadvallar | ✅ |

## Admin

| Narsa | Joy | Maydonlar |
|-------|-----|-----------|
| Asoschilar | **Sayt kontenti** → Asoschilar | photo, bio, **full_bio**, education, achievements, email, telegram, linkedin |
| O‘qituvchilar | **Foydalanuvchilar** (role=TEACHER) | avatar, specialty, bio, **full_bio**, education, achievements, telegram, show_on_homepage |
| Oy o‘quvchisi | **Sayt kontenti** → Oy o‘quvchilari | user avataridan |
| Obuna berish | Foydalanuvchilar → tanlash → 30/90/180 kun amali | ✅ (uzaytiradi) |
| Obuna so‘rovlari | **Obuna so‘rovlari** | NEW → CONTACTED → DONE |

## URL

- `/` — landing
- `/reyting/` — login required
- `/asoschi/<id>/` — asoschi to‘liq profili
- `/oqituvchi/<id>/` — o‘qituvchi to‘liq profili
- `/accounts/profile/` — profil
- `/accounts/password-reset/` — parol tiklash
- `/admin/` — boshqaruv paneli
- `/subscription/info/` — tarif + so‘rov

## O‘zgarishlar tarixi

### 2026-07-27 — UI/UX kamchiliklar (to‘lovsiz)
- Obuna sahifasi, video watch, exam UI/timer, kabinet progress, teacher tree, auth UX

### 2026-07-25 — 1–3-bosqich
- Founder / reyting / admin UI

### 2026-07-25 — 4-bosqich (batafsil profil)
- Founder: `full_bio`, `education`, `achievements`, `email`
- CustomUser: `full_bio`, `education`, `achievements`, `telegram`
- Kartochka → `/asoschi/<id>/` yoki `/oqituvchi/<id>/`
- Template: `templates/core/person_detail.html`
- Admin: “To‘liq profil” fieldset
- Seed demo yangilandi

### 2026-07-25 — 5-bosqich (batafsil profil UI/UX)
- To‘liq qayta dizayn: `static/css/person_detail.css` (alohida, cache-bust `?v=3`)
- Chapda qorong‘i panel + kichik yumaloq foto (88px)
- O‘ngda ma’lumotlar 2px borderli yumaloq ramkalarda (sarlavha + body)
- Template classlar: `.pd`, `.pd__aside`, `.pd__frame`

### 2026-07-25 — saqlash
- Backup papka: `/home/neo/Desktop/xyz_saqlangan_2026-07-25`
- Asosiy loyiha: `/home/neo/Desktop/xyz`

## Keyingi ixtiyoriy

- Onlayn to‘lov (Payme/Click) — alohida katta vazifa
- Haqiqiy foto/video yuklash
- Email tasdiqlash / obuna tugash eslatmasi

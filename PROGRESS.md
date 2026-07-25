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

## Admin

| Narsa | Joy | Maydonlar |
|-------|-----|-----------|
| Asoschilar | **Sayt kontenti** → Asoschilar | photo, bio, **full_bio**, education, achievements, email, telegram, linkedin |
| O‘qituvchilar | **Foydalanuvchilar** (role=TEACHER) | avatar, specialty, bio, **full_bio**, education, achievements, telegram, show_on_homepage |
| Oy o‘quvchisi | **Sayt kontenti** → Oy o‘quvchilari | user avataridan |
| Obuna berish | Foydalanuvchilar → tanlash → 30/90/180 kun amali | ✅ |

## URL

- `/` — landing
- `/reyting/` — login required
- `/asoschi/<id>/` — asoschi to‘liq profili
- `/oqituvchi/<id>/` — o‘qituvchi to‘liq profili
- `/accounts/profile/` — profil
- `/admin/` — boshqaruv paneli

## O‘zgarishlar tarixi

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
- Rasm kichikroq, yumaloq (oval) + mint border
- Ma’lumot / Ta’lim / Yutuqlar alohida yumaloq ramka-kartochkalarda
- Hero kartochka, badge, yumaloq social tugmalar, soft reveal animatsiya
- Template: `templates/core/person_detail.html` + `static/css/main.css`

## Keyingi ixtiyoriy

- Haqiqiy foto yuklash (admin orqali JPG)
- Profilga oylik o‘rin progress chart

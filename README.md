# XYZ

Universitet kirish imtihonlariga tayyorlaydigan onlayn ta’lim platformasi.

## Stack

- Backend: Django Templates + Service Layer
- DB: SQLite (dev, `USE_SQLITE=True`) yoki PostgreSQL
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript

## Arxitektura

```
Subject → Course → Module → Topic → Lesson
                                    ↓
                         10-savollik test to‘plami → Natija → Progress
```

## Asosiy qoidalar

- **Freemium:** `is_free_preview` belgilangan video + uning 10 talik testi bepul (barqaror).
- **Har video = 10 savol**.
- Obuna admin tomonidan beriladi yoki foydalanuvchi so‘rov yuboradi (onlayn to‘lov yo‘q).
- O‘qituvchi panel (`/teacher/`) orqali darslar va savollar CRUD.

## O‘rnatish

```bash
cd /home/neo/Desktop/xyz
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Dev: USE_SQLITE=True (.env.example da)
# Prod: USE_SQLITE=False + PostgreSQL (DB_* o‘zgaruvchilari)

python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```



## URL lar

- Sayt: `/`
- Kabinet: `/progress/dashboard/`
- Admin: `/admin/`
- O‘qituvchi: `/teacher/`
- Fanlar: `/education/subjects/`
- Obuna: `/subscription/info/`
- Parol tiklash: `/accounts/password-reset/`

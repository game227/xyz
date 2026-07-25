# XYZ

Universitet kirish imtihonlariga tayyorlaydigan onlayn ta’lim platformasi.

## Stack

- Backend: Django Templates + Service Layer
- DB: PostgreSQL
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript

## Arxitektura

```
Subject → Course → Module → Topic → Lesson
                                    ↓
                         10-savollik test to‘plami → Natija → Progress
```

## Asosiy qoidalar

- **Freemium:** birinchi video + uning 10 talik testi bepul.
- **Har video = 10 savol** (chalkashlikni oldini oladi).
- Obuna admin tomonidan beriladi.
- O‘qituvchi panel (`/teacher/`) orqali darslar va savollar CRUD.

## O‘rnatish

```bash
cd /home/neo/xyz
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# PostgreSQL: DB_NAME=xyz, user/password .env da

python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Demo loginlar

| Rol | Login | Parol |
|---|---|---|
| Admin | admin | admin12345 |
| O‘qituvchi | teacher | teacher12345 |
| Student (bepul) | student | student12345 |
| Student (obunali) | paid | paid12345 |

## URL lar

- Sayt: `/`
- Admin: `/admin/`
- O‘qituvchi: `/teacher/`
- Fanlar: `/education/subjects/`

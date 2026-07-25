"""Seed demo curriculum: har video uchun 10 ta savol + asoschilar/reyting."""
from io import BytesIO
from pathlib import Path

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.accounts.models import CustomUser
from apps.core.models import Founder, StudentOfTheMonth
from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Answer, ExamAttempt, ExamSettings, Question
from apps.subscription.services import activate_subscription


def ensure_user(username, password, **defaults):
    user, created = CustomUser.objects.get_or_create(username=username, defaults=defaults)
    if created:
        user.set_password(password)
        user.save()
    else:
        for key, value in defaults.items():
            setattr(user, key, value)
        user.save()
        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
    return user


def make_avatar_image(initials, bg=(21, 154, 106), fg=(244, 255, 249), size=512):
    """Demo uchun oddiy avatar PNG yaratadi."""
    img = Image.new('RGB', (size, size), bg)
    draw = ImageDraw.Draw(img)
    # soft circle overlay
    margin = size // 10
    draw.ellipse((margin, margin, size - margin, size - margin), fill=(15, 47, 40))
    draw.ellipse((margin * 2, margin * 2, size - margin * 2, size - margin * 2), fill=bg)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size // 3)
    except OSError:
        font = ImageFont.load_default()
    text = (initials or 'X')[:2].upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - size * 0.03), text, fill=fg, font=font)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return ContentFile(buf.getvalue(), name=f'{text.lower()}.png')


def assign_image(field, initials, filename, bg=(21, 154, 106)):
    if field.name:
        return
    content = make_avatar_image(initials, bg=bg)
    field.save(filename, content, save=True)


def make_question_bank(lesson, items, difficulty=Question.Difficulty.EASY):
    """items: list of (text, [answers], correct_idx)"""
    existing = lesson.questions.count()
    for text, answers, correct_idx in items:
        if existing >= QUESTIONS_PER_LESSON:
            break
        if lesson.questions.filter(text=text).exists():
            continue
        question = Question.objects.create(
            lesson=lesson,
            topic=lesson.topic,
            text=text,
            difficulty=difficulty,
            is_active=True,
            explanation='Demo savol.',
        )
        for idx, answer_text in enumerate(answers):
            Answer.objects.create(
                question=question,
                text=answer_text,
                is_correct=(idx == correct_idx),
                order=idx + 1,
            )
        existing += 1


class Command(BaseCommand):
    help = 'XYZ demo maʼlumotlarini yaratadi (fan, dars, asoschilar, reyting).'

    @transaction.atomic
    def handle(self, *args, **options):
        admin = ensure_user(
            'admin', 'admin12345',
            email='admin@xyz.uz', first_name='XYZ', last_name='Admin',
            role=CustomUser.Role.ADMIN, is_staff=True, is_superuser=True,
        )
        ensure_user(
            'student', 'student12345',
            email='student@xyz.uz', first_name='Ali', last_name='Karimov',
            role=CustomUser.Role.STUDENT,
        )
        paid = ensure_user(
            'paid', 'paid12345',
            email='paid@xyz.uz', first_name='Dilnoza', last_name='Saidova',
            role=CustomUser.Role.STUDENT,
        )
        activate_subscription(paid, 30, admin)
        ensure_user(
            'teacher', 'teacher12345',
            email='teacher@xyz.uz', first_name='Nodira', last_name='Aliyeva',
            role=CustomUser.Role.TEACHER,
            specialty='Algebra va funksiyalar',
            bio='10 yillik tajriba. Universitetga kirish imtihonlariga tayyorlash bo‘yicha murabbiy.',
            show_on_homepage=True,
            homepage_order=1,
        )
        ensure_user(
            'teacher2', 'teacher12345',
            email='teacher2@xyz.uz', first_name='Jasur', last_name='Rahimov',
            role=CustomUser.Role.TEACHER,
            specialty='Geometriya',
            bio='Masala yechish strategiyasi va vizual tushuntirish ustasi.',
            show_on_homepage=True,
            homepage_order=2,
        )

        subject, _ = Subject.objects.get_or_create(
            name='Matematika',
            defaults={
                'description': 'Universitet imtihoniga matematika bo‘yicha tizimli tayyorgarlik.',
                'is_active': True,
            },
        )
        Subject.objects.exclude(name='Matematika').update(is_active=False)

        course, _ = Course.objects.get_or_create(
            subject=subject,
            title='Algebra asoslari',
            defaults={'description': 'Kvadrat tenglamalar va funksiyalar.', 'order': 1, 'is_active': True},
        )
        module, _ = Module.objects.get_or_create(
            course=course,
            title='1-modul: Tenglamalar',
            defaults={'description': 'Asosiy algebraik tenglamalar.', 'order': 1, 'is_active': True},
        )
        topic1, _ = Topic.objects.get_or_create(
            module=module,
            title='Chiziqli tenglamalar',
            defaults={
                'description': 'Birinchi darajali tenglamalarni yechish.',
                'order': 1,
                'is_active': True,
                'difficulty_level': Topic.Difficulty.EASY,
            },
        )
        topic2, _ = Topic.objects.get_or_create(
            module=module,
            title='Kvadrat tenglamalar',
            defaults={
                'description': 'Diskriminant va ildizlar.',
                'order': 2,
                'is_active': True,
                'difficulty_level': Topic.Difficulty.MEDIUM,
            },
        )

        video_path = Path('media/videos/demo_intro.mp4')
        video_path.parent.mkdir(parents=True, exist_ok=True)
        if not video_path.exists() or video_path.stat().st_size < 32:
            video_path.write_bytes(b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 64)

        def ensure_lesson(topic, title, order, description):
            lesson = Lesson.objects.filter(topic=topic, title=title).first()
            if lesson:
                if not lesson.video:
                    with video_path.open('rb') as handle:
                        lesson.video.save(f'{topic.id}_{order}.mp4', File(handle), save=True)
                return lesson
            lesson = Lesson(
                topic=topic,
                title=title,
                description=description,
                order=order,
                is_active=True,
                duration_minutes=8 + order,
                created_by=admin,
            )
            with video_path.open('rb') as handle:
                lesson.video.save(f'{topic.id}_{order}.mp4', File(handle), save=True)
            return lesson

        free_lesson = ensure_lesson(
            topic1, '1-dars: Kirish (bepul)', 1,
            'Platformani sinab ko‘rish uchun bepul birinchi video.',
        )
        paid_lesson = ensure_lesson(
            topic1, '2-dars: Amaliy misollar', 2,
            'Obuna talab qilinadigan keyingi video.',
        )
        quad_lesson = ensure_lesson(
            topic2, '1-dars: Diskriminant', 1,
            'Kvadrat tenglama formulasi.',
        )

        for topic in (topic1, topic2):
            ExamSettings.objects.update_or_create(
                topic=topic,
                defaults={
                    'question_count': QUESTIONS_PER_LESSON,
                    'passing_score': 60 if topic == topic1 else 70,
                    'time_limit_minutes': 15,
                },
            )

        linear_bank = [
            (f'{a}x + {b} = {a * x + b} tenglamada x = ?', [str(x), str(x + 1), str(x - 1), str(x + 2)], 0)
            for a, b, x in [
                (2, 4, 3), (5, 0, 4), (1, -7, 10), (3, 6, 3), (1, 0, 16),
                (4, -4, 4), (2, 2, 5), (7, 7, 0), (6, -6, 2), (8, 8, 1),
            ]
        ]
        linear_bank[4] = ('x/2 = 8 bo‘lsa, x = ?', ['16', '4', '10', '12'], 0)
        linear_bank[7] = ('7x + 7 = 7 bo‘lsa, x = ?', ['0', '1', '7', '-1'], 0)

        quadratic_bank = [
            ('x² - 5x + 6 = 0 ildizlari?', ['2 va 3', '1 va 6', '-2 va -3', '0 va 5'], 0),
            ('Diskriminant D = b² - 4ac', ['To‘g‘ri', 'Noto‘g‘ri', 'Faqat juft', 'Faqat toq'], 0),
            ('x² = 9 bo‘lsa, x = ?', ['±3', '9', '3', '-9'], 0),
            ('a=1, b=-3, c=2 bo‘lsa D=?', ['1', '0', '4', '9'], 0),
            ('x² - 4 = 0 ildizlari?', ['±2', '4', '2', '0'], 0),
            ('(x-1)(x-2)=0 yechimlari?', ['1 va 2', '0 va 3', '-1 va -2', '1'], 0),
            ('Parabola yo‘nalishi a>0 bo‘lsa?', ['Yuqoriga', 'Pastga', 'Chapga', 'O‘ngga'], 0),
            ('D<0 bo‘lsa ildizlar?', ['Yo‘q (haqiqiy)', '2 ta', '1 ta', 'Cheksiz'], 0),
            ('x² + 2x + 1 = 0 ildizi?', ['-1 (ikki marta)', '1', '2', '0'], 0),
            ('Vieta: x1+x2 = ? (ax²+bx+c)', ['-b/a', 'b/a', 'c/a', '-c/a'], 0),
        ]

        make_question_bank(free_lesson, linear_bank, Question.Difficulty.EASY)
        make_question_bank(paid_lesson, linear_bank[::-1], Question.Difficulty.EASY)
        make_question_bank(quad_lesson, quadratic_bank, Question.Difficulty.MEDIUM)

        for q in Question.objects.filter(lesson__isnull=True):
            first = q.topic.lessons.order_by('order', 'id').first()
            if first:
                q.lesson = first
                q.save(update_fields=['lesson', 'updated_at'])

        founders = [
            (
                'Azizbek Xolmatov', 'Asoschi & CEO',
                'XYZ g‘oyasi muallifi. Ta’limni hamma uchun ochiq qilish.',
                'XYZ platformasini yaratish g‘oyasi muallifi. O‘quvchilarga sifatli matematika tayyorgarligini ochiq va tushunarli qilishni maqsad qilgan.',
                'Toshkent Davlat Universiteti',
                'Ta’lim startaplari, 10 000+ o‘quvchi jamoasi',
                'azizbek',
            ),
            (
                'Malika Yusupova', 'Hammuassis',
                'Kontent sifati va o‘quvchi tajribasi uchun mas’ul.',
                'Darslar, testlar va foydalanuvchi tajribasini nazorat qiladi. Har bir kontent o‘quvchi uchun aniq va foydali bo‘lishini ta’minlaydi.',
                'Pedagogika universiteti',
                'Kontent dizayni, o‘quvchi muvaffaqiyat dasturlari',
                'malika_xyz',
            ),
            (
                'Sardor Qodirov', 'Texnik asoschi',
                'Platforma arxitekturasi va o‘quv tizimini quruvchi.',
                'Texnik arxitektura, xavfsizlik va o‘quv tizimini qurgan. Platformaning barqaror ishlashi uchun javobgar.',
                'Inha University in Tashkent',
                'Full-stack tizimlar, Django/PostgreSQL',
                'sardor_dev',
            ),
        ]
        for idx, (name, title, bio, full_bio, education, achievements, tg) in enumerate(founders, start=1):
            founder, _ = Founder.objects.update_or_create(
                full_name=name,
                defaults={
                    'role_title': title,
                    'bio': bio,
                    'full_bio': full_bio,
                    'education': education,
                    'achievements': achievements,
                    'telegram': tg,
                    'order': idx,
                    'is_active': True,
                },
            )
            colors = [(21, 154, 106), (15, 47, 40), (30, 120, 95)]
            assign_image(founder.photo, name.split()[0][:1] + name.split()[-1][:1], f'founder_{idx}.png', bg=colors[idx - 1])

        student = CustomUser.objects.get(username='student')
        teacher = CustomUser.objects.get(username='teacher')
        teacher2 = CustomUser.objects.get(username='teacher2')
        teacher.specialty = 'Algebra'
        teacher.bio = 'Algebra bo‘yicha tajribali murabbiy.'
        teacher.full_bio = 'Algebra va funksiyalar bo‘yicha 8 yillik tajriba. O‘quvchilarni DTM va universitet imtihonlariga tayyorlaydi.'
        teacher.education = 'Milliy Universitet, Matematika'
        teacher.achievements = '500+ o‘quvchi tayyorlagan\nOlimpiada g‘oliblari murabbiyi'
        teacher.telegram = 'nodira_math'
        teacher.show_on_homepage = True
        teacher.homepage_order = 1
        teacher.save()
        teacher2.specialty = 'Geometriya'
        teacher2.bio = 'Geometriya va stereometriya bo‘yicha murabbiy.'
        teacher2.full_bio = 'Geometriya, stereometriya va mantiqiy masalalar bo‘yicha dars beradi. Amaliy yondashuvga e’tibor beradi.'
        teacher2.education = 'Pedagogika universiteti'
        teacher2.achievements = 'Geometriya kurslari muallifi\nOnline dars metodikasi'
        teacher2.telegram = 'jasur_geo'
        teacher2.show_on_homepage = True
        teacher2.homepage_order = 2
        teacher2.save()
        assign_image(teacher.avatar, 'NA', 'teacher_nodira.png', bg=(21, 154, 106))
        assign_image(teacher2.avatar, 'JR', 'teacher_jasur.png', bg=(15, 70, 55))
        assign_image(paid.avatar, 'DS', 'student_dilnoza.png', bg=(40, 130, 100))
        assign_image(student.avatar, 'AK', 'student_ali.png', bg=(70, 100, 90))

        now = timezone.now()
        for user, scores in (
            (paid, [95, 90, 88, 100]),
            (student, [70, 65, 80]),
        ):
            for i, score in enumerate(scores):
                lesson = free_lesson if i % 2 == 0 else paid_lesson
                if not ExamAttempt.objects.filter(user=user, lesson=lesson, score=score).exists():
                    ExamAttempt.objects.create(
                        user=user,
                        lesson=lesson,
                        topic=lesson.topic,
                        total_questions=QUESTIONS_PER_LESSON,
                        correct_answers=int(score / 10),
                        wrong_answers=QUESTIONS_PER_LESSON - int(score / 10),
                        score=score,
                        is_passed=score >= 60,
                        duration_seconds=300 + i * 40,
                    )

        StudentOfTheMonth.objects.update_or_create(
            year=now.year,
            month=now.month,
            defaults={
                'user': paid,
                'highlight': 'Eng yuqori o‘rtacha natija va faol urinishlar',
                'is_published': True,
            },
        )

        self.stdout.write(self.style.SUCCESS('XYZ demo data tayyor.'))
        self.stdout.write(f'Har video: {QUESTIONS_PER_LESSON} savol')
        self.stdout.write('Admin: admin / admin12345')
        self.stdout.write('Teacher: teacher / teacher12345')
        self.stdout.write('Student (freemium): student / student12345')
        self.stdout.write('Paid student: paid / paid12345')
        self.stdout.write('Asoschilar + reyting demo yaratildi.')

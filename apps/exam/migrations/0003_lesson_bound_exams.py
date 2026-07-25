"""
1) lesson nullable qo'shish
2) mavjud savol/urinishlarni video darsga bog'lash
3) lesson majburiy qilish
"""
import django.db.models.deletion
from django.db import migrations, models


def assign_lessons(apps, schema_editor):
    Question = apps.get_model('exam', 'Question')
    ExamAttempt = apps.get_model('exam', 'ExamAttempt')
    Lesson = apps.get_model('education', 'Lesson')

    for question in Question.objects.filter(lesson__isnull=True):
        lesson = (
            Lesson.objects.filter(topic_id=question.topic_id)
            .order_by('order', 'id')
            .first()
        )
        if lesson:
            question.lesson_id = lesson.id
            question.save(update_fields=['lesson_id'])
        else:
            question.delete()

    for attempt in ExamAttempt.objects.filter(lesson__isnull=True):
        lesson = (
            Lesson.objects.filter(topic_id=attempt.topic_id)
            .order_by('order', 'id')
            .first()
        )
        if lesson:
            attempt.lesson_id = lesson.id
            attempt.save(update_fields=['lesson_id'])
        else:
            attempt.delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0002_lesson_created_by'),
        ('exam', '0002_question_created_by'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='question',
            options={'ordering': ['id'], 'verbose_name': 'Savol', 'verbose_name_plural': 'Savollar'},
        ),
        migrations.AddField(
            model_name='question',
            name='lesson',
            field=models.ForeignKey(
                blank=True,
                help_text='Savol shu video darsning 10 talik test to‘plamiga kiradi.',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='education.lesson',
                verbose_name='video dars',
            ),
        ),
        migrations.AddField(
            model_name='examattempt',
            name='lesson',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exam_attempts',
                to='education.lesson',
                verbose_name='video dars',
            ),
        ),
        migrations.RunPython(assign_lessons, noop_reverse),
        migrations.AlterField(
            model_name='question',
            name='lesson',
            field=models.ForeignKey(
                help_text='Savol shu video darsning 10 talik test to‘plamiga kiradi.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='education.lesson',
                verbose_name='video dars',
            ),
        ),
        migrations.AlterField(
            model_name='examattempt',
            name='lesson',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exam_attempts',
                to='education.lesson',
                verbose_name='video dars',
            ),
        ),
        migrations.AlterField(
            model_name='examsettings',
            name='question_count',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Har bir video uchun qat’iy 10 ta.',
                verbose_name='savollar soni',
            ),
        ),
        migrations.AlterField(
            model_name='examsettings',
            name='passing_score',
            field=models.PositiveIntegerField(
                default=70,
                help_text='Masalan: 70, 80, 85, 90',
                verbose_name="o'tish foizi (%)",
            ),
        ),
        migrations.AlterField(
            model_name='question',
            name='topic',
            field=models.ForeignKey(
                help_text='Avtomatik: lesson.topic',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='questions',
                to='education.topic',
                verbose_name='mavzu',
            ),
        ),
    ]

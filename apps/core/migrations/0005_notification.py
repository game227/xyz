# Generated for Notification model (jonli dars + obuna bildirishnomalari)
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0004_sitesettings_branding'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='yangilangan sana')),
                ('ntype', models.CharField(choices=[('LIVE_STARTED', 'Jonli dars boshlandi'), ('SUB_ACTIVATED', 'Obuna faollashtirildi'), ('SUB_EXPIRING', 'Obuna tugash arafasida'), ('GENERAL', 'Umumiy')], default='GENERAL', max_length=20, verbose_name='turi')),
                ('title', models.CharField(max_length=200, verbose_name='sarlavha')),
                ('message', models.CharField(blank=True, max_length=400, verbose_name='matn')),
                ('url', models.CharField(blank=True, help_text='Bosilganda ochiladigan sahifa (ixtiyoriy).', max_length=300, verbose_name='havola')),
                ('is_read', models.BooleanField(default=False, verbose_name='o‘qilgan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Bildirishnoma',
                'verbose_name_plural': 'Bildirishnomalar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='core_notif_user_id_read_idx'),
        ),
    ]

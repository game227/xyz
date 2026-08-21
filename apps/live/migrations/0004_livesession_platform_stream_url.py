# Generated: jonli efir endi tashqi havola (YouTube/Telegram) orqali ishlaydi
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('live', '0003_remove_livesession_youtube_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='livesession',
            name='platform',
            field=models.CharField(choices=[('YOUTUBE', 'YouTube'), ('TELEGRAM', 'Telegram')], default='YOUTUBE', max_length=20, verbose_name='platforma'),
        ),
        migrations.AddField(
            model_name='livesession',
            name='stream_url',
            field=models.URLField(default='', help_text='YouTube jonli efir yoki Telegram kanal/efir havolasi.', verbose_name='efir havolasi'),
            preserve_default=False,
        ),
    ]

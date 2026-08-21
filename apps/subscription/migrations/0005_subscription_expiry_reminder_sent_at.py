from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0004_platform_major_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='expiry_reminder_sent_at',
            field=models.DateTimeField(blank=True, help_text='Tugashiga 5 kun qolganda avtomatik bildirishnoma yuborilgach to‘ldiriladi.', null=True, verbose_name='tugash haqida ogohlantirilgan vaqt'),
        ),
    ]

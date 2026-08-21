# Generated manually for expiry_final_reminder_sent_at

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0005_subscription_expiry_reminder_sent_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='expiry_final_reminder_sent_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Tugashiga 1 kun qolganda yakuniy eslatma yuborilgach to‘ldiriladi.',
                null=True,
                verbose_name='1 kunlik ogohlantirish vaqti',
            ),
        ),
    ]

# Generated by Django 4.2.4 on 2025-04-29 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_code_sent_at_user_is_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='verification_method',
            field=models.CharField(choices=[('email', 'Email'), ('phone', 'SMS')], default='email', max_length=10),
        ),
    ]

# Generated by Django 3.0.6 on 2020-12-24 19:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_is_test_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='guidelines',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]

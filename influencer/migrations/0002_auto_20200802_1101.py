# Generated by Django 3.0.6 on 2020-08-02 11:01

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('influencer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influencerstatistics',
            name='audience_city',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=2), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='influencerstatistics',
            name='audience_gender_age',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=2), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='influencerstatistics',
            name='follower_counts',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=2), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='influencerstatistics',
            name='impressions',
            field=django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), size=2), null=True, size=None),
        ),
    ]

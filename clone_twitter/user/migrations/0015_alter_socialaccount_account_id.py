# Generated by Django 3.2.6 on 2022-01-21 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0014_alter_profilemedia_media'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialaccount',
            name='account_id',
            field=models.BigIntegerField(),
        ),
    ]
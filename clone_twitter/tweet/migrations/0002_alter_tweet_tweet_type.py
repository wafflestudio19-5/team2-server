# Generated by Django 3.2.6 on 2021-12-28 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweet', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='tweet_type',
            field=models.CharField(choices=[('GENERAL', 'general'), ('REPLY', 'reply'), ('RETWEET', 'retweet'), ('QUOTE', 'quote_retweet')], max_length=10),
        ),
    ]

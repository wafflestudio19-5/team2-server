# Generated by Django 3.2.6 on 2021-12-31 14:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tweet', '0005_auto_20211231_0245'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quoted', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quoted_by', to='tweet.tweet')),
                ('quoting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quoting', to='tweet.tweet')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

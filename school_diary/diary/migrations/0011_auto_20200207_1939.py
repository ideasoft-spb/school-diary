# Generated by Django 3.0.2 on 2020-02-07 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0010_auto_20200207_1906'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='users',
            name='date_joined',
        ),
        migrations.AlterField(
            model_name='users',
            name='account_type',
            field=models.IntegerField(default=3, verbose_name='Тип аккаунта'),
        ),
    ]

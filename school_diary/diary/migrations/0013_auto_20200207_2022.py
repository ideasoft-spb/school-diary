# Generated by Django 3.0.2 on 2020-02-07 17:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0012_auto_20200207_2001'),
    ]

    operations = [
        migrations.AddField(
            model_name='students',
            name='grade',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='diary.Grades', verbose_name='Класс'),
        ),
        migrations.AlterField(
            model_name='users',
            name='account_type',
            field=models.IntegerField(choices=[(0, 'Root'), (1, 'Администратор'), (2, 'Учитель'), (3, 'Ученик')], default=3, verbose_name='Тип аккаунта'),
        ),
    ]
# Generated by Django 3.0.2 on 2020-01-24 22:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grades',
            name='letter',
            field=models.CharField(max_length=2, verbose_name='Буква'),
        ),
        migrations.AlterField(
            model_name='grades',
            name='main_teacher',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='diary.Teachers', verbose_name='Классный руководитель'),
        ),
        migrations.AlterField(
            model_name='grades',
            name='number',
            field=models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11)], verbose_name='Класс'),
        ),
        migrations.AlterField(
            model_name='hometasks',
            name='description',
            field=models.CharField(max_length=1000, verbose_name='Описание домашнего задания'),
        ),
        migrations.AlterField(
            model_name='hometasks',
            name='grade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diary.Grades', verbose_name='Класс'),
        ),
        migrations.AlterField(
            model_name='hometasks',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diary.Subjects', verbose_name='Предмет'),
        ),
        migrations.AlterField(
            model_name='students',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='students',
            name='grade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='diary.Grades', verbose_name='Класс'),
        ),
        migrations.AlterField(
            model_name='students',
            name='login',
            field=models.CharField(max_length=50, verbose_name='Логин'),
        ),
        migrations.AlterField(
            model_name='students',
            name='password',
            field=models.CharField(max_length=50, verbose_name='Пароль'),
        ),
        migrations.AlterField(
            model_name='students',
            name='second_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='Отчество'),
        ),
        migrations.AlterField(
            model_name='students',
            name='surname',
            field=models.CharField(max_length=50, verbose_name='Фамилия'),
        ),
        migrations.AlterField(
            model_name='subjects',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='login',
            field=models.CharField(max_length=50, verbose_name='Логин'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='password',
            field=models.CharField(max_length=50, verbose_name='Пароль'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='second_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='Отчество'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='subjects',
            field=models.ManyToManyField(to='diary.Subjects', verbose_name='Предметы'),
        ),
        migrations.AlterField(
            model_name='teachers',
            name='surname',
            field=models.CharField(max_length=50, verbose_name='Фамилия'),
        ),
    ]
# Generated by Django 3.1.2 on 2020-12-21 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=[('Информатика', 'Информатика'), ('История', 'История'), ('Литература', 'Литература'), ('Математика', 'Математика'), ('Обществознание', 'Обществознание'), ('Русский язык', 'Русский язык'), ('Химия и биология', 'Хим-Био'), ('Экономика', 'Экономика'), ('Физика', 'Физика')], max_length=20, verbose_name='Предмет')),
                ('grade', models.IntegerField(choices=[(4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11)], verbose_name='Класс')),
                ('term', models.IntegerField(choices=[(1, 'I'), (2, 'II'), (3, 'III'), (4, 'IV')], verbose_name='Четверть')),
                ('file', models.FileField(upload_to='minimum/', verbose_name='Выберите файл')),
            ],
            options={
                'verbose_name': 'Минимум',
                'verbose_name_plural': 'Минимумы',
                'ordering': ['subject', 'grade', 'term'],
            },
        ),
    ]

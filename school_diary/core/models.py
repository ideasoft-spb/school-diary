import datetime
from typing import Union

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from django.core.mail import send_mail
from django.db import models

from . import utils
from .users import manager


class Subjects(models.Model):
    name = models.CharField(
        max_length=100, verbose_name="Название",
        unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return self.name


class Klasses(models.Model):
    number = models.IntegerField(choices=settings.GRADES, verbose_name="Класс")
    letter = models.CharField(
        max_length=2, choices=settings.LETTERS, verbose_name="Буква")
    teachers = models.ManyToManyField(
        "Teachers", verbose_name="Учителя",
        related_name="klasses")
    subjects = models.ManyToManyField(Subjects, verbose_name="Предметы")
    head_teacher = models.OneToOneField(
        "Teachers", verbose_name='Классный руководитель',
        on_delete=models.SET_NULL, null=True, default=None, related_name='klass')

    class Meta:
        ordering = ['number', 'letter']
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        unique_together = ('number', 'letter')

    def __str__(self):
        return '{} {}'.format(self.number, self.letter)

    def add_new_student(self, student_id: int):
        student = Students.objects.get(pk=student_id)
        student.klass = self
        group: Groups
        for group in self.groups_set.all():
            group.students.add(student)
        student.save()


class Controls(models.Model):
    name = models.CharField(max_length=120, verbose_name='Вид работы')
    weight = models.FloatField(verbose_name='Коэффицент', default=1)

    class Meta:
        verbose_name = "Вид работы"
        verbose_name_plural = "Виды работ"

    def __str__(self):
        return "{} ({})".format(self.name, self.weight)


def lesson_upload(instance, filename):
    return 'homework/{}_{}'.format(str(instance.pk), filename)


class Lessons(models.Model):
    date = models.DateField(verbose_name='Дата')
    quarter = models.ForeignKey(
        "Quarters", on_delete=models.PROTECT, verbose_name="Четверть")
    homework = models.TextField(blank=True, verbose_name='Д/з')
    theme = models.CharField(max_length=120, verbose_name='Тема', blank=True)
    group = models.ForeignKey(
        "Groups", on_delete=models.PROTECT,
        verbose_name="Группа", null=True, default=None
    )
    control = models.ForeignKey(
        Controls, on_delete=models.PROTECT, verbose_name='Контроль')
    h_file = models.FileField(
        null=True, default=None, blank=True,
        verbose_name="Файл", upload_to=lesson_upload)
    is_planned = models.BooleanField(
        verbose_name='Запланирован', default=False)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['date']

    def __str__(self):
        return '{} {}'.format(str(self.group), self.date)


class Grades(models.Model):
    student = models.ForeignKey(
        "Students", on_delete=models.CASCADE, verbose_name="Ученик")
    amount = models.IntegerField(verbose_name="Балл", null=True, default=None)
    lesson = models.ForeignKey(
        "Lessons", on_delete=models.CASCADE, verbose_name='Урок')
    comment = models.TextField(
        blank=True, verbose_name='Комментарий', default="")

    class Meta:
        verbose_name_plural = "Оценки"
        ordering = ['lesson']

    def __str__(self):
        return '"{}" {} {}'.format(self.amount, self.lesson, self.student)

    @classmethod
    def get_data(cls, queryset) -> dict:
        """
        Take Grades QuerySet and get a smart average, average,
        qua, list of all marks' amounts, needed
        mark and a number of lesson have been missed.
        """
        data = [0, 0, 0, 0, [], 0]
        for grade in queryset:
            if grade.amount == -1:
                data[5] += 1
                continue
            if grade.lesson.control.weight != 100:
                data[0] += grade.amount * grade.lesson.control.weight
                data[1] += grade.lesson.control.weight
                data[2] += grade.amount
                data[3] += 1
                data[4].append(grade.amount)
        avg, sm_avg = utils.calculate_avg(data)
        return {
            "sm_avg": sm_avg,
            "avg": avg,
            "amount": data[3],
            "list": data[4],
            "needed": (
                utils.get_needed_mark(data[2], data[3], avg)
                if avg != '-' else '-'),
            "missed": data[5]
        }


class AdminMessages(models.Model):
    date = models.DateTimeField(
        verbose_name="Время отправки", auto_now_add=True)
    subject = models.CharField(verbose_name="Тема сообщения", max_length=100)
    content = models.TextField(verbose_name="Текст сообщения", max_length=4000)
    sender = models.ForeignKey(
        "Users", on_delete=models.CASCADE,
        verbose_name="Отправитель", null=True, default=None)
    is_read = models.BooleanField(verbose_name="Прочитанное", default=False)

    class Meta:
        verbose_name = "Сообщение администратору"
        verbose_name_plural = "Сообщения администратору"
        ordering = ['date', 'subject']

    def __str__(self):
        return self.subject


class Quarters(models.Model):
    number = models.IntegerField(verbose_name="Четверть", choices=(
        (1, "I"), (2, "II"), (3, "III"), (4, "IV")
    ), unique=True)
    begin = models.DateField(verbose_name="Начало четверти")
    end = models.DateField(verbose_name="Конец четверти")

    class Meta:
        verbose_name = "Четверть"
        verbose_name_plural = "Четверти"
        ordering = ['number']

    @classmethod
    def get_quarter_by_number(cls, number: int):
        try:
            return cls.objects.get(number=number)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_quarter_by_date(cls, date: Union[str, datetime.date]):
        """
        Return a quarter by a date stamp string.
        If quarter doesn't exist, return None instead.
        """
        date = datetime.datetime.strptime(
            date, "%Y-%m-%d"
        ).date() if isinstance(date, str) else date
        for q in cls.objects.all():
            if q.begin <= date <= q.end:
                return q
        return None

    @classmethod
    def get_current_quarter(cls):
        return cls.get_quarter_by_date(datetime.date.today())

    @classmethod
    def get_default_quarter(cls):
        def_term = cls.get_current_quarter()
        if def_term is None:
            def_term = cls.get_quarter_by_number(1)
        return def_term

    @classmethod
    def term_valid(cls, controls):
        """
        Check if teacher can create lesson with quarter grade control.
        """
        for q in cls.objects.all():
            delta = q.end - datetime.date.today()
            if delta.days < 14:
                return controls
        return controls.exclude(name='Четвертная оценка')

    @classmethod
    def year_valid(cls, controls):
        """
        Check if teacher can create lesson with year mark control.
        """
        fourth = cls.objects.get(number=4)
        delta = fourth.end - datetime.date.today()
        if delta.days < 14:
            return controls
        return controls.exclude(name='Годовая оценка')

    def __str__(self):
        return "Четверть #{}".format(self.number)


# TODO: When new student is added to grade, add him to group's students


class Groups(models.Model):
    """
    Class that combines grades and subjects.
    """
    klass = models.ForeignKey(
        "Klasses", on_delete=models.CASCADE, verbose_name="Класс")
    subject = models.ForeignKey(
        "Subjects", on_delete=models.PROTECT, verbose_name="Предмет")
    students = models.ManyToManyField(
        "Students", verbose_name="Отображаемые ученики")

    def set_default_students(self):
        qs = self.klass.students_set.all()
        self.students.set(qs)

    def get_table(self, quarter: int):
        lessons = Lessons.objects.filter(
            group=self, quarter__number=quarter, is_planned=False).order_by(
            "date").all()
        students = self.students.filter(
            klass=self.klass).order_by("account__surname")
        grades = Grades.objects.filter(
            lesson__group_id=self.id,
            lesson__quarter=quarter,
            student__in=students,
        )
        scope = self.api_process_grades(grades, students, lessons)
        return {'lessons': lessons, 'scope': scope}

    @classmethod
    def api_process_grades(cls, grades, students, lessons):
        result = []
        for student in students:
            qs = grades.filter(student=student)
            student_grades = {grade.lesson_id: grade for grade in qs}
            grades_data = Grades.get_data(qs)
            lessons_data = []
            data = {
                "student": student,
                "grades": lessons_data,
                "avg": grades_data["avg"],
                "sm_avg": grades_data["sm_avg"]
            }
            for lesson in lessons:
                if lesson.id in student_grades:
                    lessons_data.append(student_grades.get(lesson.id))
                else:
                    lessons_data.append({"lesson_id": lesson.id})
            result.append(data)
        return result

    @classmethod
    def can_use_quarter_grade(cls, controls):
        for q in Quarters.objects.all():
            delta = q.end - datetime.date.today()
            if delta.days < 14:
                return controls
        return controls.exclude(name='Четвертная оценка')

    def get_group_controls(self, quarter: int):
        controls = Controls.objects.all()
        controls = Quarters.term_valid(controls)
        controls = Quarters.year_valid(controls)
        lessons = Lessons.objects.filter(
            group=self, quarter__number=quarter).all()
        for lesson in lessons:
            if lesson.control.name == 'Четвертная оценка':
                controls = controls.exclude(name='Четвертная оценка')
            if lesson.control.name == 'Годовая оценка':
                controls = controls.exclude(name='Годовая оценка')
        return controls

    def __str__(self):
        return "{} - {}".format(self.klass, self.subject)

    @classmethod
    def create_group(cls, klass_id: int, subject_id: int):
        """
        Create a new group from given `klass_id` and `subject_id`
        and set a default students list in this group.

        Returns:
            A new Groups object if group was created successfully,
            or the group existed before, None otherwise
        """
        try:
            klass = Klasses.objects.get(id=klass_id)
            subject = Subjects.objects.get(id=subject_id)
        except (Klasses.DoesNotExist, Subjects.DoesNotExist):
            return None
        # Check if subject is studied in the class
        if subject not in klass.subjects.all():
            return None
        return cls.objects.get_or_create(klass=klass, subject=subject)[0]

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        unique_together = ("klass", "subject")


class Users(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('Почта', unique=True)
    account_type = models.IntegerField("Тип аккаунта", default=3, choices=settings.ACCOUNT_TYPES)
    is_active = models.BooleanField('Активный', default=True)
    is_staff = models.BooleanField('Администратор', default=False)

    first_name = models.CharField("Имя", max_length=100)
    second_name = models.CharField("Отчество", max_length=100, blank=True, default='')
    surname = models.CharField("Фамилия", max_length=100)

    registration_date = models.DateField("Дата регистрации", auto_now_add=True, null=True)

    objects = manager.UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['account_type']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        permissions = [
            ("edit_news", "Может редактировать статьи в новостном блоке.")
        ]

    def get_full_name(self):
        return f"{self.surname} {self.first_name} {self.second_name}"

    def get_short_name(self):
        return f"{self.surname} {self.first_name}"

    def get_username(self):
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def create_account(self):
        types = [Admins, Admins, Teachers, Students]
        model = types[self.account_type]
        return model.objects.create(account=self)

    def add_to_group(self):
        groups = {
            0: "Root", 1: "Админы",
            2: "Учителя", 3: "Ученики"
        }
        group_name = groups.get(self.account_type)
        group, create = Group.objects.get_or_create(name=group_name)
        self.groups.add(group)
        self.save()

    def is_student(self):
        return self.account_type == 3

    def is_teacher(self):
        return self.account_type == 2

    def is_admin(self):
        return self.account_type in (0, 1)

    def get_edit_form(self, *args, **kwargs):
        from .users import forms
        if self.account_type == 3:
            return forms.StudentEditForm(*args, **kwargs)
        elif self.account_type == 2:
            return forms.TeacherEditForm(*args, **kwargs)
        return forms.UserEditForm(*args, **kwargs)

    def __str__(self):
        return self.get_username()


def teacher_avatar_upload(instance, filename):
    return 'teachers/{}/{}'.format(instance.pk, filename)


class Teachers(models.Model):
    account = models.OneToOneField(
        Users, on_delete=models.CASCADE, related_name='teacher',
        verbose_name="Пользователь", primary_key=True)
    avatar = models.FileField(
        verbose_name="Аватар", null=True, default=None, blank=True,
        upload_to=teacher_avatar_upload)
    subjects = models.ManyToManyField("Subjects", verbose_name="Предметы")

    class Meta:
        verbose_name = "Учитель"
        verbose_name_plural = "Учителя"

    def __str__(self):
        return '{}'.format(self.account.get_full_name())


class Students(models.Model):
    account = models.OneToOneField(
        Users, on_delete=models.CASCADE,
        verbose_name="Пользователь", primary_key=True, related_name='student')
    klass = models.ForeignKey(
        "Klasses", on_delete=models.SET_NULL, null=True, default=None,
        verbose_name="Класс", blank=True)
    president = models.BooleanField(verbose_name="Староста", default=False)

    class Meta:
        ordering = ['klass']
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"

    def __str__(self):
        return '{} {}'.format(self.account.get_short_name(), self.klass)

    def get_grades(self, quarter: int):
        """
        Return a dictionary with student's grades for
        specified quarter sorted by groups.
        If no grades are found, `None` is returned.
        """
        groups = Groups.objects.filter(students=self, klass=self.klass)
        all_grades = self.grades_set.filter(
            lesson__quarter__number=quarter, lesson__is_planned=False)
        if not all_grades:
            return None

        d = {}
        max_length, total_missed = 0, 0
        for group in groups:
            marks = all_grades.filter(
                lesson__group=group, lesson__is_planned=False).order_by("lesson__date")
            if len(marks) > max_length:
                max_length = len(marks)
            data = Grades.get_data(marks)
            d[group] = [data['sm_avg'], data["avg"], marks]
            total_missed += data["missed"]

        for group in d:
            d[group].append(range(max_length - len(d[group][2])))
        return {
            "missed": total_missed,
            "data": d,
            "max_length": max_length
        }

    def get_grades_by_group(self, quarter: int, group_id: int):
        lessons = Lessons.objects.filter(
            group_id=group_id, quarter__number=quarter)
        all_grades = self.grades_set.filter(
            lesson__quarter__number=quarter, lesson__is_planned=False,
            lesson__group_id=group_id)
        context = {}
        if all_grades:
            context = Grades.get_data(all_grades)
        context.update({
            "lessons": lessons,
            "grades": all_grades
        })
        return context

    def get_student_grades(self, quarter: int, group_id: int):
        grades = self.grades_set.filter(
            lesson__quarter__number=quarter, lesson__is_planned=False,
            lesson__group_id=group_id)
        grades_data = Grades.get_data(grades)
        data = {
            "grades_data": grades_data,
            "grades": {
                grade.lesson: grade for grade in grades
            }
        }
        return data


class Admins(models.Model):
    account = models.OneToOneField(
        Users, on_delete=models.CASCADE,
        verbose_name="Пользователь", primary_key=True, related_name="admin")

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"

    def __str__(self):
        return '{}'.format(self.account.get_full_name())

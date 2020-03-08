from functools import reduce
import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import *
from .decorators import unauthenticated_user, admin_only, allowed_users
from .models import *


TERMS = (
    ((1, 7), (27, 10)),
    ((3, 11), (29, 12)),
    ((12, 1), (27, 3)),
    ((29, 3), (27, 5))
    )


def get_quater_by_date(datestring: str) -> int:
    """
    Returns a number of a quater by the date stamp string.
    If quater does not exit, return 0 instead.
    """
    converted_date = datetime.datetime.strptime(datestring, "%Y-%m-%d").date()
    year = converted_date.year
    for i in range(0, 4):
        start = datetime.date(year, TERMS[i][0][1], TERMS[i][0][0])
        end = datetime.date(year, TERMS[i][1][1], TERMS[i][1][0])
        if start <= converted_date <= end:
            return i+1
    else:
        return 0

@unauthenticated_user
def user_register(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Учётная запись была создана успешно.")
            return redirect('/login')
    if request.POST:
        form = StudentSignUpForm(request.POST)
    else:
        form = StudentSignUpForm()
    return render(request, 'registration.html', {'form': form, 'error': 0})


@unauthenticated_user
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            messages.info(request, 'Неправильный адрес электронной почты или пароль.')
    form = UsersLogin()
    context = {'form': form}
    return render(request, 'login.html', context)


def user_logout(request):
    logout(request)
    return redirect('/login/')


@login_required(login_url="/login/")
def user_profile(request):
    if request.user.account_type == 0:
        data = Users.objects.get(email=request.user)
    if request.user.account_type == 1:
        data = Administrators.objects.get(account=request.user)
    if request.user.account_type == 2:
        data = Teachers.objects.get(account=request.user)
    if request.user.account_type == 3:
        data = Students.objects.get(account=request.user)
    context = {'data': data}
    return render(request, 'profile.html', context)


@login_required(login_url="/login/")
@admin_only
def admin_register(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новый администратор был создан успешно.")
            return redirect('/login/')
    if request.POST:
        form = AdminSignUpForm(request.POST)
    else:
        form = AdminSignUpForm()
    return render(request, 'registration_admin.html', {'form': form, 'error': 0})


@login_required(login_url="/login/")
@admin_only
def teacher_register(request):
    if request.method == 'POST':
        form = TeacherSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Новый учитель был создан успешно.")
            return redirect('/login/')
    if request.POST:
        form = TeacherSignUpForm(request.POST)
    else:
        form = TeacherSignUpForm()
    return render(request, 'registration_teacher.html', {'form': form, 'error': 0})


@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
@login_required(login_url="/login/")  # TODO fix bug
def lesson_page(request, pk):
    lesson = Lessons.objects.get(pk=pk)
    # if request.method == 'POST':
    #     form = LessonEditForm(request.POST, instance=lesson)
    #     if form.is_valid():
    #         form.save()
    #         return HttpResponseRedirect('/diary/')
    #     else:
    #         pass
    # form = LessonEditForm(instance=lesson)
    controls = Controls.objects.all()
    controls = term_valid(controls, 3, 7)
    context = {
        'lesson': lesson,
        'controls': controls
    }
    if request.method == 'POST':
        lesson = Lessons.objects.get(pk=request.POST.get('pk'))
        lesson.date = request.POST.get('date')
        lesson.theme = request.POST.get('theme')
        lesson.control = Controls.objects.get(pk=request.POST.get('control'))
        lesson.homework = request.POST.get('homework')
        lesson.save()
        return redirect('diary')

    return render(request, 'lesson_page.html', context)


def get_average(list):
    if len(list) == 0:
        return '-'
    grades = [i.amount for i in list]
    return round(sum(grades) / len(list), 2)


def get_smart_average(list):
    if len(list) == 0:
        return "-"
    s = 0
    w = 0
    for i in list:
        weight = i.lesson.control.weight
        s += weight * i.amount
        w += weight
    return round(s / w, 2)


@login_required(login_url='/login/')
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def delete_lesson(request, pk):
    lesson = Lessons.objects.get(pk=pk)
    if request.method == "POST":
        lesson.delete()
        return redirect('diary')
    return render(request, 'lesson_delete.html', {'item':lesson})


def create_table(grade, subject, quater):
    lessons = {
        lesson.id: lesson
        for lesson in
        Lessons.objects.filter(grade=grade, subject=subject, quater=quater).select_related("control").order_by("date").all()
    }
    students = {student.account_id: student for student in
                Students.objects.filter(grade=grade).order_by("first_name", "surname", "second_name")}

    marks = Marks.objects.filter(
        student__grade_id=grade.id,
        lesson__grade_id=grade.id,
        lesson__subject_id=subject.id,
        lesson__quater=quater,
    )

    scope = {}
    for mark in marks:
        if students[mark.student_id] not in scope:
            scope[students[mark.student_id]] = {}
        lesson = lessons[mark.lesson_id]
        scope[students[mark.student_id]].update({lesson: mark})

    for sk, student in students.items():
        for lk, lesson in lessons.items():
            if student not in scope:
                scope[student] = {}
            if lesson not in scope[student]:
                scope[student].update({lesson: None})

    return {
        'is_post': True,
        'lessons': lessons,
        'scope': scope,
        'subject_id': subject.id,
        'grade_id': grade.id
    }


def term_valid(controls, month, day):
    if datetime.date(datetime.date.today().year, month, day) <= datetime.date.today() <= datetime.date(datetime.date.today().year, month, day + 7):
        return controls
    else:
        return controls.exclude(name='Четвертная')


@login_required(login_url="/login/")
def diary(request):
    """
    Main function for displaying diary pages to admins/teachers/students.
    """
    
    # If user is admin
    if request.user.account_type == 0 or request.user.account_type == 1:
        return render(request, 'diary_admin_main.html')

    # If user is student
    elif request.user.account_type == 3:
        student = Students.objects.get(account=request.user)
        grade = student.grade
        if grade is None:
            return render(request, 'access_denied.html', {'message':"Вы не состоите в классе.\
            Попросите Вашего классного руководителя добавить вас в класс."})
        if 'selected' in request.POST:
            subject = request.POST.get('subject')
            return redirect('/diary/{}'.format(subject))
        elif 'all' in request.POST:
            chosen_quater = int(request.POST.get('term'))
            subjects = grade.subjects.all()
            all_marks = student.marks_set.filter(lesson__quater=chosen_quater)
            if not all_marks: return render(request, 'no_marks.html')
            d = {}
            max_length, total_missed = 0, 0
            for s in subjects:
                marks = all_marks.filter(subject=s.id).order_by('lesson__date')

                if len(marks) > max_length:
                    max_length = len(marks)

                n_amount = 0
                marks_list = []
                for i in marks:
                    if i.amount != -1:
                        marks_list.append(i)
                    else:
                        n_amount += 1

                avg = get_average(marks_list)
                smart_avg = get_smart_average(marks_list)
                d.update({s:[avg, smart_avg, marks]})

                total_missed += n_amount

            for subject in d:
                d[subject].append(range(max_length - len(d[subject][2])))
            context = {
                'student': student,
                'd': d,
                'max_length':max_length,
                'total_missed':total_missed,
                'term':chosen_quater
            }
            return render(request,'marklist.html',context)

        subjects = grade.subjects.all()
        context = {'subjects': subjects}
        return render(request, 'diary_student.html', context)

    # If user is teacher
    elif request.user.account_type == 2:
        teacher = Teachers.objects.get(account=request.user)
        controls = Controls.objects.all()
        controls = term_valid(controls, 3, 6)
        
        context = {'Teacher': teacher,
                   'subjects': teacher.subjects.all(),
                   'grades': Grades.objects.filter(teachers=teacher),
                   'controls': controls
                   }
        if 'subject' in request.session.keys() and 'grade' in request.session.keys() and 'term' in request.session.keys():
            context.update(create_table(grade=Grades.objects.get(pk=request.session['grade']), subject=Subjects.objects.get(pk=request.session['subject']), quater=request.session['term']))


        if request.method == 'POST':
            # If teacher filled in a form with name = 'getgrade' then
            # build a table with marks for all students and render it.
            if 'getgrade' in request.POST:
                subject = Subjects.objects.get(name=request.POST.get('subject'))
                grade = request.POST.get('grade')
                request.session['subject'] = subject.id
                term = request.POST.get('term')
                request.session['term'] = int(term)
                number = int(grade[0:-1])
                letter = grade[-1]
                try:
                    grade = Grades.objects.get(number=number, subjects=subject, letter=letter, teachers=teacher)
                    request.session['grade'] = grade.id
                except ObjectDoesNotExist:
                    messages.error(request, 'Ошибка')
                    return render(request, 'teacher.html', context)

                context.update(create_table(grade, subject, term))
                return render(request, 'teacher.html', context)

            elif 'createlesson' in request.POST:
                date = request.POST.get('date')
                quater = get_quater_by_date(date)
                theme = request.POST.get('theme')
                homework = request.POST.get('homework')
                control = Controls.objects.get(id=request.POST.get('control'))
                grade = Grades.objects.get(id=request.session['grade'])
                subject = Subjects.objects.get(id=request.session['subject'])
                lesson = Lessons.objects.create(
                    date=date, quater=quater, theme=theme, homework=homework, control=control, grade=grade, subject=subject
                )
                lesson.save()
                context.update(create_table(grade=grade, subject=subject, quater=quater))
                return render(request, 'teacher.html', context)

            else:
                # Save marks block
                marks_dict = {
                    tuple(map(int, k.replace("mark_", "").split("|"))):str(request.POST[k])
                    for k in dict(request.POST)
                    if k.startswith('mark_')
                }
                subject = Subjects.objects.get(id=request.POST.get('subject_id'))

                marks_raw = Marks.objects.select_for_update().filter(
                    student__grade_id=request.POST.get('grade_id'),
                    lesson__grade_id=request.POST.get('grade_id'),
                    lesson__subject_id=subject.id
                )

                marks_in_db = {
                    (x.student_id, x.lesson_id): x
                    for x in marks_raw
                }

                objs_for_update = []
                for k, v in marks_dict.items():
                    if v != "" and k in marks_in_db.keys() and marks_in_db[k].amount != int(v):
                        marks_in_db[k].amount = int(v)
                        objs_for_update.append(marks_in_db[k])

                objs_for_create = [
                    Marks(lesson_id=k[1], student_id=k[0], amount=int(v), subject=subject)
                    for k, v in marks_dict.items()
                    if v != "" and k not in marks_in_db.keys()
                ]

                objs_for_remove = [
                    Q(id=marks_in_db[k].id)
                    for k, v in marks_dict.items()
                    if v == "" and k in marks_in_db
                ]
                Marks.objects.bulk_update(objs_for_update, ['amount'])

                Marks.objects.bulk_create(objs_for_create)

                if len(objs_for_remove) != 0:
                    Marks.objects.filter(reduce(lambda a, b: a | b, objs_for_remove)).delete()

                print("Added ", len(objs_for_create), " Changed ", len(objs_for_update), " Removed ", len(objs_for_remove))
                # Render table
                context.update(create_table(grade=Grades.objects.get(pk=request.session['grade']), subject=subject, quater=request.session['term']))
                return render(request, 'teacher.html', context) # For debug
                # return redirect(diary)
        else:
            return render(request, 'teacher.html', context)
    else:
        redirect('/')


@login_required(login_url="login")
@allowed_users(allowed_roles=['students'], message="Доступ к этой странице имеют только ученики.")
def stats(request, id):
    student = Students.objects.get(account=request.user)
    grade = student.grade
    try:
        subject = Subjects.objects.get(id=id)
    except ObjectDoesNotExist:
        return render(request,'error.html', context={'title':'Мы не можем найти то, что Вы ищите.',
                                                     'error':'404',
                                                     'description':'Данный предмет отстуствует.'})
    #return HttpResponse(subject.name)
    lessons = Lessons.objects.filter(grade=grade, subject=subject)
    #return HttpResponse(len(lessons))
    marks = []
    #for i in lessons:
        #try: marks.append(Marks.objects.get(student=student, lesson=i))
        #except: pass
    marks = student.marks_set.filter(subject=subject)

    # If student has no marks than send him a page with info.
    # Otherwise, student will get a page with statistics and his results.
    if marks:
        n_amount = 0
        marks_list = []
        for i in marks:
            if i.amount != -1:
                marks_list.append(i)
            else:
                n_amount += 1

        avg = get_average(marks_list)
        smart_avg = get_smart_average(marks_list)

        marks_amounts = [i.amount for i in marks if i.amount != -1]
        data = []
        for i in range(5, 1, -1): data.append(marks_amounts.count(i))
        data.append(n_amount)

        context = {
            'lessons':lessons,
            'marks':marks,
            'subject':subject,
            'data':data,
            'avg':avg,
            'smartavg':smart_avg}
        return render(request, 'results.html', context)
    return render(request, 'no_marks.html')
    subjects = grade.subjects.all()
    context = {'subjects':subjects}
    return render(request, 'diary_student.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['students'], message="Доступ к этой странице имеют только ученики.")
def homework(request):
    if request.method == "POST":
        if "day" in request.POST:
            form = DatePickForm(request.POST)
            if form.is_valid():
                date = form.cleaned_data['date']
                student = Students.objects.get(account=request.user)
                grade = student.grade
                lessons = Lessons.objects.filter(date=date, grade=grade)
            return render(request, 'homework.html', {'form':form, 'lessons':lessons, 'date':date})
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=6)
    lessons = Lessons.objects.filter(date__range=[start_date, end_date])
    form = DatePickForm()
    return render(request, 'homework.html', {'form':form, 'lessons':lessons})


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def add_student_page(request):
    """
    Page where teachers can add students to their grade.
    """
    try:
        grade = Grades.objects.get(main_teacher=request.user.id)
    except ObjectDoesNotExist:
        return render(request, 'access_denied.html', {'message': "Вы не классный руководитель."})
    students = Students.objects.filter(grade=grade)

    if request.method == "POST":
        form = AddStudentToGradeForm(request.POST)
        if form.is_valid:
            fn = request.POST.get('first_name')
            s = request.POST.get('surname')
            search = Students.objects.filter(first_name=fn, surname=s)
            context = {'form': form, 'search': search, 'grade': grade, 'students': students}
            return render(request, 'grades/add_student.html', context)

    form = AddStudentToGradeForm()
    context = {'form': form, 'grade': grade, 'students': students}
    return render(request, 'grades/add_student.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def add_student(request, i):
    """
    Function defining the process of adding new student to a grade and confirming it.
    """
    u = Users.objects.get(email=i)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        try:
            grade = Grades.objects.get(main_teacher=request.user.id)
            s.grade = grade
            s.save()
            return redirect('add_student_page')
        except ObjectDoesNotExist:
            context = {'message': "Вы не классный руководитель."}
            return render(request, 'access_denied.html', context)
    else:
        return render(request, 'grades/add_student_confirm.html', {'s': s})


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def create_grade_page(request):
    if request.method == "POST":
        form = GradeCreationForm(request.POST)
        if form.is_valid():
            grade = form.save()
            mt = Teachers.objects.get(account=request.user)
            grade.main_teacher = mt
            grade.save()
            return redirect('my_grade')
    form = GradeCreationForm()
    context = {'form': form}
    return render(request, 'grades/add_grade.html', context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def my_grade(request):
    """
    Page with information about teacher's grade.
    """
    me = Teachers.objects.get(account=request.user)
    try:
        grade = Grades.objects.get(main_teacher=me)
    except ObjectDoesNotExist:
        grade = None
    context = {'grade': grade}
    return render(request, 'grades/my_grade.html', context)


def view_students_marks(request):
    me = Teachers.objects.get(account=request.user)
    try:
        grade = Grades.objects.get(main_teacher=me)
        students = Students.objects.filter(grade=grade)
        context = {
            'students':students
        }
        return render(request, 'grades/grade_marks.html', context)
    except ObjectDoesNotExist:
        return render(request, 'access_denied.html', {'message': 'Вы не являетесь классным руководителем.'})


def get_class_or_access_denied(teacher):
    try:
        my_class = Grades.objects.get(main_teacher=teacher)
        return my_class
    except ObjectDoesNotExist:
        return render(request, 'access_denied.html', {'message': 'Вы не являетесь классным руководителем.'})


def students_marks(request, pk):
    student = Students.objects.get(account=pk)
    me = Teachers.objects.get(account=request.user)
    my_class = get_class_or_access_denied(me)

    subjects = my_class.subjects.all()
    all_marks = student.marks_set.all()
    d = {}
    max_length, total_missed = 0, 0
    for s in subjects:
        marks = all_marks.filter(subject=s.id).order_by('lesson__date')

        if len(marks) > max_length:
            max_length = len(marks)

        n_amount = 0
        marks_list = []
        for i in marks:
            if i.amount != -1:
                marks_list.append(i)
            else:
                n_amount += 1

        avg = get_average(marks_list)
        smart_avg = get_smart_average(marks_list)
        d.update({s:[avg, smart_avg, marks]})
        total_missed += n_amount


    for subject in d:
        d[subject].append(range(max_length - len(d[subject][2])))
    context = {
        'student': student,
        'd': d,
        'max_length':max_length,
        'total_missed':total_missed
    }
    return render(request,'view_marks.html',context)


@login_required(login_url="login")
@allowed_users(allowed_roles=['teachers'], message="Вы не зарегистрированы как учитель.")
def delete_student(request, i):
    """
    Function defining the process of deleting a student from a grade and confirming it.
    """
    u = Users.objects.get(email=i)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        try:
            grade = Grades.objects.get(main_teacher=request.user.id)
            s.grade = None
            s.save()
            return redirect('add_student_page')
        except ObjectDoesNotExist:
            context = {'message': "Вы не классный руководитель."}
            return render(request, 'access_denied.html', context)
    else:
        return render(request, 'grades/delete_student_confirm.html', {'s': s})


@allowed_users(allowed_roles=['teachers', 'students'], message="Вы не зарегистрированы как учитель или ученик.")
@login_required(login_url="login")
def admin_message(request):
    """
    Send a message to an admin.
    """
    if request.method == "POST":
        form = AdminMessageCreationForm(request.POST)
        if form.is_valid():
            m = form.save()
            m.sender = request.user
            m.save()
            return redirect('profile')
    form = AdminMessageCreationForm()
    return render(request, 'admin_messages.html', {'form': form})


@login_required(login_url="/login/")
@admin_only
def students_dashboard_first_page(request):
    return redirect('/students/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def students_dashboard(request, page):
    """
    Send a dashboard with up to 100 students.
    TODO: Test a pagination.
    """
    students = Students.objects.all()
    students = Paginator(students, 100)
    students = students.get_page(page)
    return render(request, 'students/dashboard.html', {'students': students})


@login_required(login_url="/login/")
@admin_only
def students_delete(request, id):
    """
    Delete a student.
    """
    u = Users.objects.get(email=id)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('students_dashboard')
    return render(request, 'students/delete.html', {'s': s})


@login_required(login_url="/login/")
@admin_only
def students_update(request, id):
    """
    Edit student's account info.
    """
    u = Users.objects.get(email=id)
    s = Students.objects.get(account=u)
    if request.method == "POST":
        form = StudentEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('students_dashboard')
    form = StudentEditForm(instance=s)
    return render(request, 'students/update.html', {'form': form})


@login_required(login_url="/login/")
@admin_only
def admins_dashboard_first_page(request):
    """
    Redirect user to the first page of admin dashboard.
    """
    return redirect('/admins/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def admins_dashboard(request, page):
    """
    Send dashboard with up to 100 administrators
    """
    u = Administrators.objects.all()
    u = Paginator(u, 100)
    u = u.get_page(page)
    return render(request, 'admins/dashboard.html', {'users': u})


@login_required(login_url="/login/")
@admin_only
def admins_delete(request, id):
    """
    Delete an admin.
    """
    u = Users.objects.get(email=id)
    s = Administrators.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('admins_dashboard')
    return render(request, 'admins/delete.html', {'s': s})


@login_required(login_url="/login/")
@admin_only
def admins_update(request, id):
    """
    Edit admin's info.
    """
    u = Users.objects.get(email=id)
    s = Administrators.objects.get(account=u)
    if request.method == "POST":
        form = AdminsEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('admins_dashboard')
    form = AdminsEditForm(instance=s)
    return render(request, 'admins/update.html', {'form': form})


# TEACHERS SECTION

@login_required(login_url="/login/")
@admin_only
def teachers_dashboard_first_page(request):
    return redirect('/teachers/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def teachers_dashboard(request, page):
    u = Teachers.objects.all()
    u = Paginator(u, 50)
    u = u.get_page(page)
    return render(request, 'teachers/dashboard.html', {'users': u})


@login_required(login_url="/login/")
@admin_only
def teachers_delete(request, id):
    """
    Delete a teacher.
    """
    u = Users.objects.get(email=id)
    s = Teachers.objects.get(account=u)
    if request.method == "POST":
        u.delete()
        s.delete()
        return redirect('teachers_dashboard')
    return render(request, 'teachers/delete.html', {'s': s})


@login_required(login_url="/login/")
@admin_only
def teachers_update(request, id):
    """
    Edit teachers's account info.
    """
    u = Users.objects.get(email=id)
    s = Teachers.objects.get(account=u)
    if request.method == "POST":
        form = TeacherEditForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            return redirect('teachers_dashboard')
    form = TeacherEditForm(instance=s)
    return render(request, 'teachers/update.html', {'form': form})


def homepage(request):
    """
    Return a homepage.
    """
    return render(request, 'homepage.html')


def social(request):
    """
    Return a page with link to gymnasium's social pages.
    """
    return render(request, 'social.html')


def get_help(request):
    """
    Return a page with help information.
    """
    return render(request, 'docs.html')


def error404(request):
    return render(request, 'error.html', {
        'error': "404",
        'title': "Страница не найдена.",
        "description": "Мы не можем найти страницу, которую Вы ищите."
    })


def error500(request):
    return render(request, 'error.html', {
        'error': "500",
        'title': "Что-то пошло не так",
        "description": "Мы работаем над этим."
    })


@login_required(login_url="/login/")
@admin_only
def messages_dashboard_first_page(request):
    """
    Redirect user to the first page of admin dashboard.
    """
    return redirect('/messages/dashboard/1')


@login_required(login_url="/login/")
@admin_only
def messages_dashboard(request, page):
    u = AdminMessages.objects.all()
    u = Paginator(u, 100)
    u = u.get_page(page)
    return render(request, 'messages/dashboard.html', {'users': u})


@login_required(login_url="/login/")
@admin_only
def messages_delete(request, pk):
    s = AdminMessages.objects.get(id=pk)
    if request.method == "POST":
        s.delete()
        return redirect('messages_dashboard')
    return render(request, 'messages/delete.html', {'s': s})


@login_required(login_url="/login/")
@admin_only
def messages_view(request, pk):
    s = AdminMessages.objects.get(id=pk)
    return render(request, 'messages/view.html', {'s': s})




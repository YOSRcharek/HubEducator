from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import AddUserForm, EditUserForm
from core.models import User, Course,CourseCategory, Lesson, SubLesson, Resource
from etude.models import GroupeEtude
from etude.forms import GroupeEtudeForm

# --------------------------
# Teacher Dashboard
# --------------------------
@login_required
def TeacherDash(request):
    if request.user.role != 'teacher':
        return redirect(reverse('unauthorized'))
    return render(request, 'teacherDash.html', {})


# --------------------------
# List Students assigned to teacher's courses
# --------------------------
@login_required
def students(request):
    if request.user.role != 'teacher':
        return redirect(reverse('unauthorized'))

    # Récupérer tous les étudiants inscrits aux cours de cet enseignant
    students_list = User.objects.filter(
        role='student',
        enrolled_courses__teacher=request.user
    ).distinct()

    paginator = Paginator(students_list, 5)  # 5 étudiants par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'students/students.html', {'page_obj': page_obj})


# --------------------------
# Add a new student
# --------------------------
@login_required
def add_student(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))

    if request.method == "POST":
        form = AddUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'  # s'assurer que c'est un student
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, "Student added successfully!")
            return redirect('students')  # redirige vers la liste des students
    else:
        form = AddUserForm()

    return render(request, 'students/addstudent.html', {'form': form})


# --------------------------
# Edit a student
# --------------------------
@login_required
def edit_student(request, user_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse("unauthorized"))

    student = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = EditUserForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully!")
            return redirect("students")
    else:
        form = EditUserForm(instance=student)

    return render(request, "students/editstudent.html", {"form": form, "student_obj": student})


# --------------------------
# Delete a student
# --------------------------
@login_required
def delete_student(request, user_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))

    student = get_object_or_404(User, id=user_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect('students')

@login_required
def student_detail(request, user_id):
    if request.user.role != 'teacher':
        return redirect(reverse('unauthorized'))

    student = get_object_or_404(User, pk=user_id)

    # Récupérer les cours de l’étudiant liés à cet enseignant
    courses = student.enrolled_courses.filter(teacher=request.user)

    return render(request, 'students/student_detail.html', {
        'student': student,
        'courses': courses
    })

@login_required
def courses(request):
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    # Récupérer tous les cours de l'enseignant connecté
    courses_list = Course.objects.filter(teacher=request.user).distinct()

    # Pagination : 5 cours par page
    paginator = Paginator(courses_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'courses/courses.html', {'page_obj': page_obj})


@login_required
def add_courses(request):
    if request.method == 'POST':
        # 1️⃣ Enregistrer le cours de l’étape 1
        title = request.POST.get('title')
        description = request.POST.get('description')
        capacity = request.POST.get('capacity', 30)
        category = request.POST.get('category')
        category_obj = CourseCategory.objects.filter(name=category).first() if category else None

        course = Course.objects.create(
            title=title,
            description=description,
            capacity=capacity,
            category=category_obj,
            teacher=request.user
        )

        # 2️⃣ Ajouter les lessons dynamiques (LESSON_TITLE_1, LESSON_TITLE_2, ...)
        lesson_count = int(request.POST.get('lesson_count', 0))
        lessons_dict = {}  # mapping ID temporaire → objet Lesson réel

        for i in range(1, lesson_count + 1):
            lesson_title = request.POST.get(f'LESSON_TITLE_{i}')
            lesson_description = request.POST.get(f'LESSON_DESCRIPTION_{i}', '')
            lesson_order = request.POST.get(f'LESSON_ORDER_{i}', 0)

            lesson_obj = Lesson.objects.create(
                course=course,
                title=lesson_title,
                description=lesson_description,
                order=lesson_order
            )
            lessons_dict[str(i)] = lesson_obj  # stocker pr lier les SubLessons

        # 3️⃣ Ajouter les sub-lessons dynamiques (pareil structure)
        sublesson_count = int(request.POST.get('sublesson_count', 0))

        for j in range(1, sublesson_count + 1):
            sub_title = request.POST.get(f'SUBLESSON_TITLE_{j}')
            sub_content = request.POST.get(f'SUBLESSON_CONTENT_{j}')
            attach_lesson_index = request.POST.get(f'SUBLESSON_LESSON_{j}')
            attach_lesson = lessons_dict.get(attach_lesson_index)

            SubLesson.objects.create(
                lesson=attach_lesson,
                title=sub_title,
                content=sub_content
            )

        # ✅ 4️⃣ (optionnel pour l’instant) : gérer les fichiers Dropzone ici

        return redirect('courses')  # Nom de ta page après succès

    else:
        categories = CourseCategory.objects.all()
        return render(request, 'courses/addCourses.html', {'categories': categories})

@login_required
def teacher_groupes(request):
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    groupes = GroupeEtude.objects.filter(createur=request.user)
    return render(request, 'etude/groupes.html', {'groupes': groupes})

# --------------------------
# Add etude group 
# --------------------------
@login_required
def add_groupe(request):
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')

        if nom:
            GroupeEtude.objects.create(
                nom=nom,
                description=description,
                createur=request.user
            )
            messages.success(request, "Study group created successfully!")
            return redirect('teacher_groupes')  

    return render(request, 'etude/addGroupe.html')
    # --------------------------
# Edit a group
# --------------------------
@login_required
def edit_group(request, group_id):
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    groupe = get_object_or_404(GroupeEtude, id=group_id, createur=request.user)

    if request.method == "POST":
        form = GroupeEtudeForm(request.POST, instance=groupe)
        if form.is_valid():
            form.save()
            messages.success(request, "Group updated successfully!")
            return redirect('teacher_groups')  # redirect to alias name used in templates
    else:
        form = GroupeEtudeForm(instance=groupe)

    # Render the actual template you have in TeacherDash/templates/etude/
    return render(request, 'etude/editGroupe.html', {'form': form, 'groupe': groupe})


@login_required
def delete_group(request, group_id):
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    groupe = get_object_or_404(GroupeEtude, id=group_id, createur=request.user)

    if request.method == "POST":
        groupe.delete()
        messages.success(request, "Group deleted successfully!")
        return redirect('teacher_groups')

    return render(request, 'etude/deleteGroupe.html', {'groupe': groupe})
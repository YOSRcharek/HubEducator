from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import AddUserForm, EditUserForm
from core.models import User, Course


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

# --------------------------
# Profile view
# --------------------------
@login_required
def profil(request):
    return render(request, 'profil.html', {})


#---------------
# courses
#-------------
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
    return render(request, 'courses/addCourses.html', {})
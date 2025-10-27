from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import AddUserForm, EditUserForm
from core.models import User, Course, CertificateAttempt, Speciality, CertificatExercise, Certificate
from django.views import View
from django.utils.decorators import method_decorator
from .forms import SpecialityForm, CertificateForm, CertificatExerciseForm
from django.forms import modelformset_factory
from django.db import transaction
import csv
from django.http import HttpResponse
from openpyxl import Workbook


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

@method_decorator(login_required, name='dispatch')
class SpecialityListView(View):
    def get(self, request):
        specialities = Speciality.objects.all()
        return render(request, 'specialities/listSpecialities.html', {'specialities': specialities})

@method_decorator(login_required, name='dispatch')
class SpecialityCreateView(View):
    def get(self, request):
        form = SpecialityForm()
        return render(request, 'specialities/addSpecialities.html', {'form': form})

    def post(self, request):
        form = SpecialityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('specialities')  # corriger nom url
        return render(request, 'specialities/addSpecialities.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class SpecialityUpdateView(View):
    def get(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        form = SpecialityForm(instance=speciality)
        return render(request, 'specialities/editSpecialities.html', {'form': form})

    def post(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        form = SpecialityForm(request.POST, instance=speciality)
        if form.is_valid():
            form.save()
            return redirect('specialities')
        return render(request, 'specialities/editSpecialities.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class SpecialityDeleteView(View):
    def post(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        speciality.delete()
        return redirect('specialities')

class ListCertificatView(View):
    def get(self, request):
        search_query = request.GET.get('search', '')
        certificates_qs = Certificate.objects.annotate(
            exercise_count=Count('exercises'),
            participant_count=Count('certificateattempt', distinct=True),
            succeeded_count=Count('certificateattempt', filter=Q(certificateattempt__passed=True), distinct=True)
        ).all().order_by('id')

        if search_query:
            certificates_qs = certificates_qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(speciality__name__icontains=search_query)
            )

        if search_query:
            certificates = certificates_qs
            page_obj = None
        else:
            paginator = Paginator(certificates_qs, 10)  # 10 items per page
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            certificates = page_obj.object_list

        return render(request, 'certificats/listCertificate.html', {
            'certificates': certificates,
            'page_obj': page_obj,
            'search_query': search_query
        })


@login_required
def create_certificate(request):
    CertificatExerciseFormSet = modelformset_factory(
        CertificatExercise,
        form=CertificatExerciseForm,
        extra=1,  # une ligne vide par défaut
        can_delete=True
    )

    exercise_error = None

    if request.method == 'POST':
        cert_form = CertificateForm(request.POST, request.FILES)
        formset = CertificatExerciseFormSet(
            request.POST,
            queryset=CertificatExercise.objects.none(),
            prefix='exercise'
        )

        if cert_form.is_valid() and formset.is_valid():
            exercises_to_save = []
            has_empty_exercise = False

            for form in formset:
                if not form.cleaned_data.get('DELETE'):
                    exercise_type = form.cleaned_data.get('exercise_type')
                    has_data = (
                        form.cleaned_data.get('question') or
                        form.cleaned_data.get('option1') or
                        form.cleaned_data.get('option2') or
                        form.cleaned_data.get('option3') or
                        form.cleaned_data.get('option4')
                    )
                    if has_data and not exercise_type:
                        has_empty_exercise = True
                        break
                    elif exercise_type:
                        exercises_to_save.append(form)

            if has_empty_exercise:
                exercise_error = "All exercises must have an exercise type selected."
            elif not exercises_to_save:
                exercise_error = "At least one exercise is required."
            else:
                certificate = cert_form.save()
                for form in exercises_to_save:
                    exercise = form.save(commit=False)
                    exercise.certificate = certificate
                    exercise.save()
                messages.success(request, "Certificate created successfully!")
                return redirect('list_certificates')
        else:
            exercise_error = "Please correct the errors in the exercises."
    else:
        cert_form = CertificateForm()
        formset = CertificatExerciseFormSet(
            queryset=CertificatExercise.objects.none(),
            prefix='exercise'
        )

    specialities = Speciality.objects.all()
    return render(request, 'certificats/certificate_form.html', {
        'cert_form': cert_form,
        'formset': formset,
        'exercise_error': exercise_error,
        'specialities': specialities,
    })


# AJOUT / MODIF: edit_certificate (passer et traiter formset avec exercises existants)
@login_required
def edit_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, pk=cert_id)
    CertificatExerciseFormSet = modelformset_factory(
        CertificatExercise,
        form=CertificatExerciseForm,
        extra=0,  # pas de formulaire vide automatiquement
        can_delete=True
    )

    exercise_error = None

    if request.method == "POST":
        cert_form = CertificateForm(request.POST, request.FILES, instance=certificate)
        formset = CertificatExerciseFormSet(
            request.POST,
            queryset=CertificatExercise.objects.filter(certificate=certificate),
            prefix='exercise'
        )

        if cert_form.is_valid() and formset.is_valid():
            exercises_to_save = []
            has_empty_exercise = False

            for form in formset:
                if not form.cleaned_data.get('DELETE'):
                    exercise_type = form.cleaned_data.get('exercise_type')
                    has_data = (
                        form.cleaned_data.get('question') or
                        form.cleaned_data.get('option1') or
                        form.cleaned_data.get('option2') or
                        form.cleaned_data.get('option3') or
                        form.cleaned_data.get('option4')
                    )
                    if has_data and not exercise_type:
                        has_empty_exercise = True
                        break
                    elif exercise_type:
                        exercises_to_save.append(form)

            if has_empty_exercise:
                exercise_error = "All exercises must have an exercise type selected."
            elif not exercises_to_save:
                exercise_error = "At least one exercise is required."
            else:
                try:
                    with transaction.atomic():
                        cert_form.save()
                        for form in formset.forms:
                            if form.cleaned_data.get('DELETE') and form.instance.pk:
                                form.instance.delete()
                            elif form.cleaned_data.get('exercise_type'):
                                exercise = form.save(commit=False)
                                exercise.certificate = certificate
                                exercise.save()
                        messages.success(request, "Certificate updated successfully!")
                        return redirect('list_certificates')
                except Exception as e:
                    messages.error(request, f"Error updating certificate: {str(e)}")
        else:
            exercise_error = "Please correct the errors in the exercises."
    else:
        cert_form = CertificateForm(instance=certificate)
        formset = CertificatExerciseFormSet(
            queryset=CertificatExercise.objects.filter(certificate=certificate),
            prefix='exercise'
        )

    specialities = Speciality.objects.all()
    return render(request, 'certificats/editCertificate.html', {
        'cert_form': cert_form,
        'formset': formset,
        'certificate': certificate,
        'exercise_error': exercise_error,
        'specialities': specialities,
    })

# AJOUT: delete_certificate
@login_required
def delete_certificate(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    if request.method == "POST":
        certificate.delete()
        messages.success(request, "Certificate deleted successfully.")
        return redirect('list_certificates')
    # If not POST, redirect back to list
    return redirect('list_certificates')

@login_required
def preview_certificate(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    exercises = CertificatExercise.objects.filter(certificate=certificate)
    return render(request, 'certificats/preview_certificate.html', {
        'certificate': certificate,
        'exercises': exercises,
    })

@login_required
def certificate_results(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    attempts = CertificateAttempt.objects.filter(certificate=certificate).select_related('user').order_by('-completed_at')
    return render(request, 'certificats/certificate_results.html', {
        'certificate': certificate,
        'attempts': attempts,
    })

@login_required
def attempt_details(request, attempt_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    attempt = get_object_or_404(CertificateAttempt, pk=attempt_id)
    answers = attempt.answers.select_related('exercise').all()
    return render(request, 'certificats/attempt_details.html', {
        'attempt': attempt,
        'answers': answers,
    })

@login_required
def export_certificate_results_csv(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    attempts = CertificateAttempt.objects.filter(certificate=certificate).select_related('user').prefetch_related('answers__exercise').order_by('-completed_at')

    # Get all exercises for this certificate
    exercises = list(CertificatExercise.objects.filter(certificate=certificate).order_by('id'))

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Certificate Results"

    # Write headers
    headers = ['User', 'Score', 'Total Questions', 'Passed', 'Completed At']
    for exercise in exercises:
        headers.append(f"{exercise.question} - Answer")
        headers.append(f"{exercise.question} - Correct Answer")

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data
    for row_num, attempt in enumerate(attempts, 2):
        ws.cell(row=row_num, column=1, value=attempt.user.username)
        ws.cell(row=row_num, column=2, value=attempt.score)
        ws.cell(row=row_num, column=3, value=attempt.total_questions)
        ws.cell(row=row_num, column=4, value='Yes' if attempt.passed else 'No')
        ws.cell(row=row_num, column=5, value=attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S'))

        # Create a dict of exercise_id to answer for quick lookup
        answers_dict = {answer.exercise_id: answer for answer in attempt.answers.all()}

        col_num = 6
        for exercise in exercises:
            if exercise.id in answers_dict:
                answer = answers_dict[exercise.id]
                ws.cell(row=row_num, column=col_num, value=answer.answer)
                ws.cell(row=row_num, column=col_num + 1, value=exercise.correct_answer)
            else:
                ws.cell(row=row_num, column=col_num, value='')
                ws.cell(row=row_num, column=col_num + 1, value=exercise.correct_answer)
            col_num += 2

    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{certificate.title}_results.xlsx"'

    wb.save(response)
    return response

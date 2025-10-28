from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import AddUserForm, EditUserForm
from core.models import User, Course,CourseCategory, Lesson, SubLesson, Resource,Review
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.db.models import Avg
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

    # ⚡ Mettre à jour le status des cours en fonction des leçons
    teacher_courses = Course.objects.filter(teacher=request.user)
    for course in teacher_courses:
        if course.lessons.exists() and course.status == 'pending':
            course.status = 'inprogress'
            course.save()
        elif not course.lessons.exists() and course.status != 'pending':
            course.status = 'pending'
            course.save()

    # Filtre par status
    status_filter = request.GET.get('status', '')  # vide = tous
    if status_filter:
        courses_list = teacher_courses.filter(status=status_filter)
    else:
        courses_list = teacher_courses

    # Pagination : 6 cours par page
    paginator = Paginator(courses_list.distinct(), 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Options de status pour le filtre
    status_options = ['pending', 'inprogress', 'completed']

    return render(request, 'courses/courses.html', {
        'page_obj': page_obj,
        'status_options': status_options,
        'current_status': status_filter,
    })

@login_required
def add_courses(request):
    categories = CourseCategory.objects.all()

    if request.method == 'POST':
        errors = []

        title = request.POST.get('title', '').strip()
        if not title:
            errors.append("Course title is required.")

        capacity = request.POST.get('capacity')
        try:
            capacity = int(capacity)
            if capacity <= 0:
                errors.append("Capacity must be a positive number.")
        except:
            capacity = 30  # valeur par défaut

        category_name = request.POST.get('category')
        category_obj = CourseCategory.objects.filter(name=category_name).first() if category_name else None
        if not category_obj:
            errors.append("Please select a valid category.")

        lesson_titles = request.POST.getlist('lesson_title[]')
        if not lesson_titles or all(not t.strip() for t in lesson_titles):
            errors.append("At least one lesson is required.")

        # si erreurs -> réafficher form avec messages
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'courses/addCourses.html', {'categories': categories})

        # ✅ Pas d'erreur, créer le cours
        description = request.POST.get('description', '').strip()
        course = Course.objects.create(
            title=title,
            description=description,
            capacity=capacity,
            category=category_obj,
            teacher=request.user,
            status='pending'
        )

        thumbnail_file = request.FILES.get('thumbnail')
        if thumbnail_file:
            course.thumbnail.save(thumbnail_file.name, thumbnail_file)

        lessons_dict = {}
        lesson_descriptions = request.POST.getlist('lesson_description[]')
        for idx, title_lesson in enumerate(lesson_titles, start=1):
            desc = lesson_descriptions[idx-1] if idx-1 < len(lesson_descriptions) else ''
            lesson_obj = Lesson.objects.create(course=course, title=title_lesson, description=desc, order=idx)
            lessons_dict[idx] = lesson_obj

            for file in request.FILES.getlist(f'lesson_resources_{idx}[]'):
                Resource.objects.create(lesson=lesson_obj, sub_lesson=None, title=file.name, resource_type='pdf', file=file)

        # sublessons
        sublesson_titles = request.POST.getlist('sublesson_title[]')
        sublesson_contents = request.POST.getlist('sublesson_content[]')
        lesson_objs = list(lessons_dict.values())
        for idx, sub_title in enumerate(sublesson_titles, start=1):
            content = sublesson_contents[idx-1] if idx-1 < len(sublesson_contents) else ''
            attach_lesson = lesson_objs[(idx-1) % len(lesson_objs)]
            sublesson_obj = SubLesson.objects.create(lesson=attach_lesson, title=sub_title, content=content)

            for file in request.FILES.getlist(f'sublesson_resources_{idx}[]'):
                Resource.objects.create(lesson=None, sub_lesson=sublesson_obj, title=file.name, resource_type='pdf', file=file)

        messages.success(request, "Course created successfully!")
        return redirect('courses')

    return render(request, 'courses/addCourses.html', {'categories': categories})

@login_required
def course_edit(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    categories = CourseCategory.objects.all()

    if request.method == 'POST':
        # Update basic fields
        course.title = request.POST.get('title', '').strip()
        course.description = request.POST.get('description', '').strip()

        # ✅ Update capacity proprement
        capacity = request.POST.get('capacity')
        if capacity and capacity.isdigit():
            course.capacity = int(capacity)

        # ✅ Si tu as un champ "level" dans le formulaire
        course.level = request.POST.get('level') or course.level

        # ✅ Si tu as ajouté start_date et end_date
        course.start_date = request.POST.get('start_date') or course.start_date
        course.end_date = request.POST.get('end_date') or course.end_date

        # ✅ Update category
        category_name = request.POST.get('category')
        category_obj = CourseCategory.objects.filter(name=category_name).first()
        if category_obj:
            course.category = category_obj

        # ✅ Update thumbnail s’il est modifié
        thumbnail_file = request.FILES.get('thumbnail')
        if thumbnail_file:
            course.thumbnail.save(thumbnail_file.name, thumbnail_file)

        # ✅ Sauvegarde finale
        course.save()

        messages.success(request, "Course updated successfully!")
        return redirect('courses')

    return render(request, 'courses/course_edit.html', {
        'course': course,
        'categories': categories,
    })

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect('courses')
    return render(request, 'courses/confirm_delete.html', {'course': course})

@login_required
def course_detail(request, course_id):
    # Vérifier que l'utilisateur est teacher
    if request.user.role != 'teacher':
        return redirect('unauthorized')

    course = get_object_or_404(Course, pk=course_id, teacher=request.user)

    # Leçons
    lessons = Lesson.objects.filter(course=course).order_by('order')

    # Préparer les ressources des leçons et sublessons
    import json
    from django.core.serializers.json import DjangoJSONEncoder

    for lesson in lessons:
        lesson.resource_list = Resource.objects.filter(lesson=lesson, sub_lesson__isnull=True)
        lesson.resources_json = json.dumps(
            list(lesson.resource_list.values('id', 'title', 'file', 'resource_type')),
            cls=DjangoJSONEncoder
        )

        sub_lessons = SubLesson.objects.filter(lesson=lesson).order_by('order')
        for sub in sub_lessons:
            sub.resource_list = Resource.objects.filter(sub_lesson=sub)
            sub.resources_json = json.dumps(
                list(sub.resource_list.values('id', 'title', 'file', 'resource_type')),
                cls=DjangoJSONEncoder
            )
        lesson.sublessons = sub_lessons

    # Étudiants
    students = course.students.all()
    all_students = User.objects.filter(role='student').exclude(id__in=students)

    # Durée
    if course.start_date and course.end_date:
        total_days = (course.end_date - course.start_date).days
        duration_weeks = total_days // 7
        duration_days = total_days % 7
    else:
        duration_weeks = duration_days = None

    # ✅ Reviews
    reviews = course.reviews.all().order_by('-created_at')  # les plus récents d'abord
    for review in reviews:
        review.full_stars = review.rating
        review.empty_stars = 5 - review.rating
        # Likes
        review.likes_count = review.likes.count()
        review.user_liked = request.user in review.likes.all()

        # Temps relatif type "2 hours ago"
        delta = timezone.now() - review.created_at
        if delta.days >= 1:
            review.time_ago = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            review.time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            review.time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            review.time_ago = "Just now"

    # ⭐ Moyenne des étoiles
    avg_rating = course.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_full_stars = int(avg_rating)
    avg_empty_stars = 5 - avg_full_stars

    return render(request, 'courses/detailsCourse.html', {
        'course': course,
        'lessons': lessons,
        'students': students,
        'all_students': all_students,
        'duration_weeks': duration_weeks,
        'duration_days': duration_days,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'avg_full_stars': avg_full_stars,
        'avg_empty_stars': avg_empty_stars,
    })

@login_required
def add_lesson(request):
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        lesson = Lesson.objects.create(course=course, title=title, description=description, order=Lesson.objects.filter(course=course).count() + 1)

        for file in request.FILES.getlist('resources'):
            Resource.objects.create(
                lesson=lesson,
                title=file.name,
                resource_type='pdf',  # tu peux détecter selon extension
                file=file
            )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def add_sublesson(request):
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        title = request.POST.get('title')
        content = request.POST.get('content', '')
        sublesson = SubLesson.objects.create(
            lesson=lesson,
            title=title,
            content=content,
            order=SubLesson.objects.filter(lesson=lesson).count() + 1
        )
        for file in request.FILES.getlist('resources'):
            Resource.objects.create(
                sub_lesson=sublesson,
                title=file.name,
                resource_type='pdf',
                file=file
            )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Delete Lesson
@login_required
def delete_lesson(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
        lesson.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

# Delete SubLesson
@login_required
def delete_sublesson(request, sublesson_id):
    if request.method == 'POST':
        sub = get_object_or_404(SubLesson, id=sublesson_id, lesson__course__teacher=request.user)
        sub.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

# Update Lesson
@login_required
def update_lesson(request):
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)

        # Mise à jour basique
        lesson.title = request.POST.get('title')
        lesson.description = request.POST.get('description')
        lesson.save()

        # Suppression des ressources cochées
        resources_to_delete = request.POST.getlist('delete_resources[]')
        if resources_to_delete:
            Resource.objects.filter(id__in=resources_to_delete).delete()

        # Ajout des nouvelles
        for file in request.FILES.getlist('resources'):
            Resource.objects.create(
                lesson=lesson, 
                title=file.name, 
                resource_type='pdf', 
                file=file
            )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def update_sublesson(request):
    if request.method == 'POST':
        sublesson_id = request.POST.get('sublesson_id')
        sub = get_object_or_404(SubLesson, id=sublesson_id, lesson__course__teacher=request.user)

        sub.title = request.POST.get('title')
        sub.content = request.POST.get('content')
        sub.save()

        for file in request.FILES.getlist('resources'):
            Resource.objects.create(sub_lesson=sub, title=file.name, resource_type='pdf', file=file)

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def get_lesson_resources(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, course__teacher=request.user)
    resources = list(lesson.resources.values('id', 'title', 'file'))
    return JsonResponse({'resources': resources})

@login_required
@csrf_exempt
def toggle_visibility(request, type, id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Méthode non autorisée"})

    try:
        data = json.loads(request.body)
        visible = data.get("visible", False)

        from core.models import Course, Lesson, SubLesson
        model_map = {
            "course": Course,
            "lesson": Lesson,
            "sublesson": SubLesson
        }

        model = model_map.get(type)
        if not model:
            return JsonResponse({"success": False, "error": "Type invalide"})

        obj = model.objects.get(id=id)
        obj.visible = visible
        obj.save()

        return JsonResponse({"success": True, "visible": obj.visible})
    except Exception as e:
        print("❌ Erreur toggle_visibility:", e)
        return JsonResponse({"success": False, "error": str(e)})

@login_required
def assign_students_to_course(request, course_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        student_ids = data.get('students', [])  # ⚠️ doit matcher le body JS
        course = get_object_or_404(Course, id=course_id)
        course.students.add(*User.objects.filter(id__in=student_ids, role='student'))
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def remove_student_from_course(request, course_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        student_id = data.get('student_id')
        course = get_object_or_404(Course, id=course_id)

        student = get_object_or_404(User, id=student_id, role='student')
        course.students.remove(student)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def toggle_like_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    user = request.user

    if user in review.likes.all():
        review.likes.remove(user)
        liked = False
    else:
        review.likes.add(user)
        liked = True

    return JsonResponse({'liked': liked, 'likes_count': review.likes.count()})


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Seul le propriétaire ou un professeur peut supprimer
    if request.user == review.student or request.user.role == 'teacher':
        review.delete()
        return JsonResponse({'deleted': True})
    else:
        return JsonResponse({'deleted': False, 'error': 'Unauthorized'}, status=403)
    review = get_object_or_404(Review, id=review_id)
    user = request.user

    if user in review.likes.all():
        review.likes.remove(user)
        liked = False
    else:
        review.likes.add(user)
        liked = True

    return JsonResponse({'liked': liked, 'likes_count': review.likes.count()})
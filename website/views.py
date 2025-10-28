from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from .forms import RegisterForm
from core.decorators import unauthenticated_user
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django import forms
from django.utils.crypto import get_random_string
import requests
from django.contrib.auth import get_user_model, login
from django.core.paginator import Paginator
from core.models import Course
from django.contrib.auth.decorators import login_required
from core.models import Course, Lesson, SubLesson, Resource, User , Review
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.db.models import Avg
from django.http import HttpResponseForbidden
import requests

User = get_user_model()  # Always use custom user

# ----------------------------- Public Pages -----------------------------
def home(request):
    return render(request, 'home.html', {})

def pricing(request):
    return render(request, 'pricing.html', {})

@login_required
def mycourses(request):
    enrolled_courses = Course.objects.filter(students=request.user, visible=True).order_by('-created_at')
    paginator = Paginator(enrolled_courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_courses = enrolled_courses.count()

    return render(request, 'cours/mycourses.html', {
        'page_obj': page_obj,
        'total_courses': total_courses,
    })
    
def courses(request):
    courses_list = Course.objects.filter(visible=True).order_by('-created_at')
    paginator = Paginator(courses_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cours/courses.html', {
        'page_obj': page_obj,
    })

def user_research(request):
    return render(request, 'user-research.html', {})




@login_required
def courseDetails(request, course_id):
    course = get_object_or_404(
        Course,
        id=course_id,
        visible=True  # ✅ Ne montrer que les cours actifs
    )

    # 🚨 Vérifier que l'utilisateur est inscrit à ce cours
    if request.user not in course.students.all():
        return HttpResponseForbidden("🚫 Vous n'êtes pas autorisé à accéder à ce cours. Veuillez d'abord vous inscrire.")

    teacher = course.teacher
    lessons = Lesson.objects.filter(course=course, visible=True).order_by('order')

    for lesson in lessons:
        lesson.resource_list = Resource.objects.filter(
            lesson=lesson,
            sub_lesson__isnull=True
        ).order_by('order')

        lesson.resources_json = json.dumps(
            list(lesson.resource_list.values('id', 'title', 'file', 'resource_type')),
            cls=DjangoJSONEncoder
        )

        sub_lessons = SubLesson.objects.filter(
            lesson=lesson,
            visible=True
        ).order_by('order')

        for sub in sub_lessons:
            sub.resource_list = Resource.objects.filter(sub_lesson=sub).order_by('order')
            sub.resources_json = json.dumps(
                list(sub.resource_list.values('id', 'title', 'file', 'resource_type')),
                cls=DjangoJSONEncoder
            )

        lesson.sublessons = sub_lessons

    # ✅ Reviews
    reviews = course.reviews.all().order_by('-created_at')
    for review in reviews:
        review.full_stars = review.rating or 0
        review.empty_stars = 5 - review.full_stars
        review.user_liked = request.user in review.likes.all()
        review.likes_count = review.likes.count()

    # Moyenne des notes
    avg_rating = course.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_full_stars = int(avg_rating)
    avg_empty_stars = 5 - avg_full_stars

    # Durée
    if course.start_date and course.end_date:
        total_days = (course.end_date - course.start_date).days
        duration_weeks = total_days // 7
        duration_days = total_days % 7
    else:
        duration_weeks = duration_days = None

    return render(request, 'cours/courseDetails.html', {
        'course': course,
        'lessons': lessons,
        'duration_weeks': duration_weeks,
        'duration_days': duration_days,
        'teacher': teacher,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'avg_full_stars': avg_full_stars,
        'avg_empty_stars': avg_empty_stars,
        'star_range': range(1, 6),
    })

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, visible=True)

    # Vérifier si l'utilisateur est déjà inscrit
    if request.user in course.students.all():
        messages.info(request, "You are already enrolled in this course.")
        return redirect('courseDetails', course_id=course.id)

    # Ajouter l'utilisateur aux étudiants
    course.students.add(request.user)
    messages.success(request, "You have successfully enrolled in the course!")

    return redirect('courseDetails', course_id=course.id)

# ----------------------------- Authentication -----------------------------

@unauthenticated_user
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)

            if user is not None:
                if not user.email_verified:
                    messages.error(request, "You must verify your email before logging in.")
                    return redirect("verify_code")

                auth_login(request, user)
                messages.success(request, "Connecté avec succès.")
                
                if user.role == 'admin':
                    return redirect('dashboard')
                elif user.role == 'teacher':
                    return redirect('teacherDash')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Email ou mot de passe invalide.")
        except User.DoesNotExist:
            messages.error(request, "Aucun compte avec cet email.")

    # 🔹 En cas de GET ou d’échec, on rend la page de login
    return render(request, "login.html", {
        'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID,
        'GOOGLE_REDIRECT_URI': settings.GOOGLE_REDIRECT_URI,
    })


@unauthenticated_user
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            

            # Send verification code
            send_verification_code(user)
            messages.success(request, "Compte créé — un code de vérification a été envoyé à votre email.")
            return redirect("verify_code")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("login")

# ----------------------------- Verification -----------------------------
def send_verification_code(user):
    code = get_random_string(length=6, allowed_chars='0123456789')
    user.verification_code = code
    user.save()

    subject = "Your Verification Code"
    message = f"Hi {user.username},\n\nYour verification code is: {code}\n\nEnter it in your platform to verify your email."
    from_email = f"HubEducator <{settings.DEFAULT_FROM_EMAIL}>"
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)


class VerifyCodeForm(forms.Form):
    code = forms.CharField(max_length=6, label="Verification Code")


def verify_code_view(request):
    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                user = User.objects.get(verification_code=code)
                user.email_verified = True
                user.verification_code = ''
                user.save()
                messages.success(request, "Your email is verified!")
                return redirect("login")
            except User.DoesNotExist:
                messages.error(request, "Invalid verification code.")
    else:
        form = VerifyCodeForm()
    return render(request, "verify_code.html", {"form": form})


def resend_code_view(request):
    user_id = request.session.get('user_id')  # Get user id from session
    if not user_id:
        messages.error(request, "Unable to resend code. Please login again.")
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        send_verification_code(user)
        messages.success(request, "A new verification code has been sent to your email.")
    except User.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('verify_code')

# ----------------------------- Password Reset -----------------------------
def custom_password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "User with this email does not exist.")
                return redirect('password_reset')

            # Generate token and link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"

            # HTML email with inline styles
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>Password Reset</title></head>
            <body style="font-family:Arial,sans-serif; background:#f8f9fa; margin:0; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); text-align:center;">
                    <img src="https://hubeducator-production.up.railway.app/static/website/img/favicons/android-chrome-192x192.png" width="100" alt="HubEducator Logo" style="margin-bottom:20px;">
                    <h1 style="font-size:24px; margin:20px 0;">Reset Your Password</h1>
                    <p style="font-size:16px;">Hi {user.username},</p>
                    <p style="font-size:16px;">Click the button below to reset your password:</p>
                    <a href="{reset_link}" style="display:inline-block; padding:12px 25px; color:#fff; background-color:#FFD700; border-radius:8px; text-decoration:none; font-weight:600;">Reset Password</a>
                    <p style="margin-top:20px; font-size:14px; color:#555;">If you didn't request this, you can ignore this email.</p>
                </div>
            </body>
            </html>
            """
            text_content = f"Hi {user.username},\nReset your password here: {reset_link}"

            email_message = EmailMultiAlternatives(
                subject="Reset Your Password",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            messages.success(request, "Password reset email sent successfully.")
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'ResetPassword/password_reset.html', {'form': form})


def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('/')

    # Échange du code contre un token
    token_req = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
    )
    token_data = token_req.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return redirect('/')  # Gérer l’erreur si nécessaire

    # Récupérer les infos utilisateur
    user_req = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        params={'access_token': access_token}
    )
    user_data = user_req.json()

    # Créer ou récupérer l'utilisateur
    user, created = User.objects.get_or_create(email=user_data['email'])
    if created:
        user.username = user_data.get('name', user_data['email'])
        user.save()

    # Connecter l'utilisateur
    login(request, user)
    return redirect('/')

@login_required
def submit_review(request, course_id):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        course = get_object_or_404(Course, id=course_id)
        rating = int(request.POST.get('rating', 0))
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')

        review = Review.objects.create(
            course=course,
            student=request.user,
            rating=rating,
            title=title,
            content=content
        )

        # Préparer la réponse JSON
        return JsonResponse({
            'success': True,
            'review': {
                'student': request.user.get_full_name() or request.user.username,
                'rating': review.rating,
                'title': review.title,
                'content': review.content,
                'created_at': review.created_at.strftime('%d %b %Y')
            }
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

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

    if request.user == review.student or request.user.role == 'teacher':
        review.delete()
        return JsonResponse({'deleted': True})
    else:
        return JsonResponse({'deleted': False, 'error': 'Unauthorized'}, status=403)


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if request.user != review.student:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method == "POST":
        title = request.POST.get('title', review.title)
        content = request.POST.get('content', review.content)
        rating = request.POST.get('rating', review.rating)

        review.title = title
        review.content = content
        review.rating = rating
        review.save()

        return JsonResponse({
            'success': True,
            'title': review.title,
            'content': review.content,
            'rating': review.rating
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
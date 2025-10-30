from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from tutor_ai.pdf_summarizer import summarize_pdf_file 
from tutor_ai.course_recommender import recommend_for_student
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
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import requests
import json
from core.models import Subscription
from django.contrib.auth import get_user_model, login
from django.core.paginator import Paginator
from core.models import Course
from django.contrib.auth.decorators import login_required
from core.models import Course, Lesson, SubLesson, Resource, User , Review ,SubLessonProgress
from django.views.decorators.http import require_POST
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.db.models import Avg
from django.http import HttpResponseForbidden
import requests
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import Certificate, Speciality, CertificatExercise, CertificateAttempt, CertificateAnswer, Subscription
from openai import OpenAI
from django.template.loader import render_to_string

User = get_user_model()  # Always use custom user

# ----------------------------- Public Pages -----------------------------
def home(request):
    return render(request, 'home.html', {})

def pricing(request):
    """Display all active subscriptions for users, separated by type"""
    student_subscriptions = Subscription.objects.filter(is_active=True, user_type='student').order_by('created_at')
    teacher_subscriptions = Subscription.objects.filter(is_active=True, user_type='teacher').order_by('created_at')
    
    return render(request, 'pricing.html', {
        'student_subscriptions': student_subscriptions,
        'teacher_subscriptions': teacher_subscriptions,
    })

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
    # Récupérer les cours visibles
    courses_list = Course.objects.filter(visible=True).order_by('-created_at')
    paginator = Paginator(courses_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    student = request.user if request.user.is_authenticated else None
    recs = recommend_for_student(student) if student else []

    return render(request, 'cours/courses.html', {
        'page_obj': page_obj,
        'recommendations': recs,
    })

def user_research(request):
    return render(request, 'user-research.html', {})



@login_required
def courseDetails(request, course_id):
    course = get_object_or_404(Course, id=course_id, visible=True)

    if request.user not in course.students.all():
        return HttpResponseForbidden("🚫 Vous n'êtes pas autorisé à accéder à ce cours. Veuillez d'abord vous inscrire.")

    teacher = course.teacher
    lessons = Lesson.objects.filter(course=course, visible=True).order_by('order')

    # ✅ Calcul de progression pour chaque leçon
    for lesson in lessons:
        lesson.resource_list = Resource.objects.filter(lesson=lesson, sub_lesson__isnull=True).order_by('order')
        lesson.resources_json = json.dumps(
            list(lesson.resource_list.values('id', 'title', 'file', 'resource_type')),
            cls=DjangoJSONEncoder
        )

        sub_lessons = SubLesson.objects.filter(lesson=lesson, visible=True).order_by('order')
        for sub in sub_lessons:
            sub.resource_list = Resource.objects.filter(sub_lesson=sub).order_by('order')
            sub.resources_json = json.dumps(
                list(sub.resource_list.values('id', 'title', 'file', 'resource_type')),
                cls=DjangoJSONEncoder
            )

        lesson.sublessons = sub_lessons

        # ✅ Progression de la leçon
        total_subs = sub_lessons.count()
        completed_subs = SubLessonProgress.objects.filter(
            student=request.user,
            sub_lesson__in=sub_lessons,
            completed=True
        ).count()

        if total_subs > 0:
            lesson.progress = round((completed_subs / total_subs) * 100, 1)
        else:
            lesson.progress = 0

    # ✅ Progression totale du cours
    all_sublessons = SubLesson.objects.filter(lesson__course=course, visible=True)
    completed_sublessons = SubLessonProgress.objects.filter(
        student=request.user,
        sub_lesson__in=all_sublessons,
        completed=True
    ).count()
    total_sublessons = all_sublessons.count()
    course.progress = round((completed_sublessons / total_sublessons) * 100, 1) if total_sublessons > 0 else 0

    # ✅ Reviews, durée, etc. (inchangé)
    reviews = course.reviews.all().order_by('-created_at')
    for review in reviews:
        review.full_stars = review.rating or 0
        review.empty_stars = 5 - review.full_stars
        review.user_liked = request.user in review.likes.all()
        review.likes_count = review.likes.count()

    avg_rating = course.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_full_stars = int(avg_rating)
    avg_empty_stars = 5 - avg_full_stars

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


@login_required
def unenroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user in course.students.all():
        course.students.remove(request.user)
        messages.success(request, f"Vous avez été désinscrit du cours « {course.title} »")
    return redirect('coursesUser')

@login_required
def lesson_details(request, course_id, lesson_id):
    # Récupérer le cours et vérifier qu'il est visible
    course = get_object_or_404(Course, id=course_id, visible=True)

    # Vérifier que l'utilisateur est inscrit au cours
    if request.user not in course.students.all():
        return HttpResponseForbidden("🚫 You are not authorized to access this lesson.")

    # Récupérer la leçon
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course, visible=True)

    # Récupérer les sous-leçons et leurs ressources
    sub_lessons = lesson.sub_lessons.prefetch_related('resources').order_by('order').all()
    for sub in sub_lessons:
        sub.resource_list = sub.resources.all().order_by('order')
        sub.resources_json = json.dumps(
            list(sub.resource_list.values('id', 'title', 'file', 'resource_type', 'external_url')),
            cls=DjangoJSONEncoder
        )

    # Récupérer les ressources de la leçon principale
    lesson.resource_list = lesson.resources.filter(sub_lesson__isnull=True).order_by('order')
    lesson.resources_json = json.dumps(
        list(lesson.resource_list.values('id', 'title', 'file', 'resource_type', 'external_url')),
        cls=DjangoJSONEncoder
    )

    # Progression (exemple : remplacer avec ton vrai calcul si tu as un modèle Completion)
    completed_count = 0
    total_count = sub_lessons.count()
    progress_percent = int((completed_count / total_count) * 100) if total_count else 0

    # Calcul de la durée du cours
    if course.start_date and course.end_date:
        total_days = (course.end_date - course.start_date).days
        duration_weeks = total_days // 7
        duration_days = total_days % 7
    else:
        duration_weeks = duration_days = None

    # Reviews du cours
    reviews = course.reviews.all().order_by('-created_at')
    avg_rating = course.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_full_stars = int(avg_rating)
    avg_empty_stars = 5 - avg_full_stars
    
   # 🔹 Progression réelle à partir du modèle SubLessonProgress
    completed_subs = SubLessonProgress.objects.filter(
        student=request.user, sub_lesson__in=sub_lessons, completed=True
    ).values_list('sub_lesson_id', flat=True)

    completed_count = len(completed_subs)
    total_count = sub_lessons.count()
    progress_percent = int((completed_count / total_count) * 100) if total_count else 0

    
    context = {
        'course': course,
        'lesson': lesson,
        'sub_lessons': sub_lessons,
        'completed_count': completed_count,
        'completed_subs': list(completed_subs),
        'total_count': total_count,
        'progress_percent': progress_percent,
        'teacher': course.teacher,
        'duration_weeks': duration_weeks,
        'duration_days': duration_days,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'avg_full_stars': avg_full_stars,
        'avg_empty_stars': avg_empty_stars,
        'star_range': range(1, 6),
    }

    return render(request, 'cours/lessonDetails.html', context)

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
        'GOOGLE_URL': settings.GOOGLE_URL,
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
            # messages.success(request, "Compte créé — un code de vérification a été envoyé à votre email.")
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
                # messages.success(request, "Your email is verified!")
                
                # Auto-login after verification
                auth_login(request, user)
                if user.role == 'admin':
                    return redirect('dashboard')
                elif user.role == 'teacher':
                    return redirect('teacherDash')
                else:
                    return redirect('home')
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
    'client_id': GOOGLE_CLIENT_ID,
    'client_secret': GOOGLE_CLIENT_SECRET,
    'redirect_uri': GOOGLE_REDIRECT_URI,
    'grant_type': 'authorization_code',  # Google OAuth
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


# ----------------------------- Payment System -----------------------------
@login_required
def initiate_payment(request, subscription_id):
    """Initiate payment for a subscription"""
    subscription = get_object_or_404(Subscription, id=subscription_id, is_active=True)
    
    # Get currency and amount from query parameters
    selected_currency = request.GET.get('currency', 'USD').upper()
    selected_amount = request.GET.get('amount', str(subscription.price))
    
    # Map of unsupported currencies to supported ones with conversion rates
    unsupported_currencies = {
        'TND': {'stripe_currency': 'usd', 'rate': 3.1},  # TND to USD
        'MAD': {'stripe_currency': 'usd', 'rate': 10.2}  # MAD to USD
    }
    
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Check if currency is supported by Stripe
        amount_float = float(selected_amount)
        display_currency = selected_currency
        display_amount = selected_amount
        
        if selected_currency in unsupported_currencies:
            # Convert to supported currency for Stripe
            conversion_info = unsupported_currencies[selected_currency]
            stripe_currency = conversion_info['stripe_currency']
            rate = conversion_info['rate']
            amount_float = amount_float / rate  # Convert back to USD
        else:
            stripe_currency = selected_currency.lower()
        
        # Convert amount to cents/smallest currency unit
        amount_in_cents = int(amount_float * 100)
        
        # Create a PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=stripe_currency,
            metadata={
                'subscription_id': subscription.id,
                'user_id': request.user.id,
                'user_email': request.user.email,
                'display_currency': display_currency,
                'display_amount': display_amount
            },
            description=f'{subscription.name} subscription for {request.user.email}'
        )
        
        # Store info in session
        request.session['subscription_id'] = subscription.id
        request.session['payment_intent_id'] = payment_intent.id
        request.session['client_secret'] = payment_intent.client_secret
        request.session['payment_currency'] = display_currency
        request.session['payment_amount'] = display_amount
        
        return render(request, 'payment/checkout.html', {
            'subscription': subscription,
            'client_secret': payment_intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'currency': display_currency,
            'amount': display_amount,
        })
        
    except Exception as e:
        messages.error(request, f"Error initiating payment: {str(e)}")
        return redirect('pricing')


@login_required
def process_payment(request):
    """Confirm payment after Stripe Elements submission"""
    if request.method == 'POST':
        try:
            import stripe
            from core.models import Transaction, UserSubscription
            from datetime import timedelta
            from django.utils import timezone
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Get payment intent ID from session
            payment_intent_id = request.session.get('payment_intent_id')
            subscription_id = request.session.get('subscription_id')
            
            if not payment_intent_id or not subscription_id:
                messages.error(request, "Invalid payment session")
                return redirect('pricing')
            
            # Retrieve the PaymentIntent to check its status
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            subscription = get_object_or_404(Subscription, id=subscription_id)
            
            if payment_intent.status == 'succeeded':
                # Create transaction record
                transaction, created = Transaction.objects.get_or_create(
                    stripe_payment_intent_id=payment_intent.id,
                    defaults={
                        'user': request.user,
                        'subscription': subscription,
                        'amount': subscription.price,
                        'currency': 'usd',
                        'status': 'completed',
                        'description': f'{subscription.name} subscription',
                        'completed_at': timezone.now()
                    }
                )
                
                if created:
                    # Calculate end date based on duration
                    # Simple parsing - you can make this more sophisticated
                    duration_days = 30  # Default
                    if 'month' in subscription.duration.lower():
                        duration_days = 30
                    elif 'year' in subscription.duration.lower():
                        duration_days = 365
                    elif 'day' in subscription.duration.lower():
                        import re
                        days_match = re.search(r'(\d+)', subscription.duration)
                        if days_match:
                            duration_days = int(days_match.group(1))
                    
                    # Deactivate all existing active subscriptions for this user
                    UserSubscription.objects.filter(
                        user=request.user,
                        is_active=True
                    ).update(is_active=False)
                    
                    # Create user subscription
                    UserSubscription.objects.create(
                        user=request.user,
                        subscription=subscription,
                        transaction=transaction,
                        end_date=timezone.now() + timedelta(days=duration_days),
                        is_active=True
                    )
                
                    # Clear session
                for key in ['subscription_id', 'payment_intent_id', 'client_secret']:
                    if key in request.session:
                        del request.session[key]
                
                # Update user role based on subscription type
                if subscription.user_type == 'teacher':
                    request.user.role = 'teacher'
                    request.user.save()
                    return redirect('teacherDash')
                else:  # student subscription
                    request.user.role = 'student'
                    request.user.save()
                    return redirect('home')
            else:
                messages.error(request, f"Payment status: {payment_intent.status}")
                return redirect('payment_failed')
            
        except Exception as e:
            messages.error(request, f"Payment processing error: {str(e)}")
            return redirect('payment_failed')
    
    return redirect('pricing')


@login_required
def payment_success(request):
    """Payment success page"""
    if request.user.role == 'teacher':
        return render(request, 'payment/success_teacher.html')
    else:
        return render(request, 'payment/success_student.html')


@login_required
def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payment/failed.html')


# ----------------------------- Stripe Webhook -----------------------------
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    import stripe
    from core.models import Transaction, UserSubscription
    from datetime import timedelta
    from django.utils import timezone
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            event = json.loads(payload)
        
        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            # Update transaction status
            try:
                transaction = Transaction.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.save()
                
                print(f"✅ Payment succeeded for transaction {transaction.id}")
                
            except Transaction.DoesNotExist:
                print(f"⚠️ Transaction not found for payment_intent: {payment_intent['id']}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            
            # Update transaction status
            try:
                transaction = Transaction.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                transaction.status = 'failed'
                transaction.save()
                
                print(f"❌ Payment failed for transaction {transaction.id}")
                
            except Transaction.DoesNotExist:
                print(f"⚠️ Transaction not found for payment_intent: {payment_intent['id']}")
        
        return HttpResponse(status=200)
        
    except ValueError as e:
        # Invalid payload
        print(f"❌ Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"❌ Invalid signature: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return HttpResponse(status=500)

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


@csrf_exempt
def schedule_course(request, course_id):
    if request.method == "POST":
        data = json.loads(request.body)
        date_str = data.get("publish_date")
        if not date_str:
            return JsonResponse({"error": "Date manquante"}, status=400)

        # Conversion string -> datetime
        publish_date = timezone.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        publish_date = timezone.make_aware(publish_date)  # rend timezone-aware si USE_TZ=True

        course = Course.objects.get(id=course_id)
        course.publish_date = publish_date
        course.visible = False  # assure que ce sera publié plus tard
        course.save()
        return JsonResponse({"success": True})


@csrf_exempt
def ask_ai(request):
    """
    Endpoint pour poser des questions à l'IA en fonction de la ressource affichée.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        question = data.get("question")
        resource_url = data.get("resource_url")
        resource_type = data.get("resource_type")

        # Extraction du contenu selon le type de ressource
        content_text = ""
        if resource_type == "pdf":
            # Télécharger le PDF temporairement
            response = requests.get(resource_url)
            with open("temp.pdf", "wb") as f:
                f.write(response.content)
            reader = PdfReader("temp.pdf")
            content_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif resource_type in ["image", "video", "audio"]:
            content_text = f"Ressource de type {resource_type} : {resource_url}"
        else:
            content_text = "Contenu non exploitable."

        # Préparer le prompt pour l'IA
        prompt = f"""
        Voici le contenu de la ressource :\n{content_text}\n
        Question : {question}\n
        Réponds de manière claire, concise et adaptée à ce contenu.
        """

        # Appel à OpenAI GPT
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        answer = response.choices[0].message["content"]

        return JsonResponse({"answer": answer})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def summarize_pdf_view(request):
    if request.method == "POST":
        try:
            file = request.FILES.get('pdf')
            if not file:
                return JsonResponse({"error": "No PDF uploaded"}, status=400)

            summary = summarize_pdf_file(file)
            return JsonResponse({"summary": summary})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "POST method required"}, status=400)






@require_POST
@login_required
def toggle_sublesson_completion(request, sublesson_id):
    sublesson = get_object_or_404(SubLesson, id=sublesson_id)
    user = request.user

    progress, created = SubLessonProgress.objects.get_or_create(
        student=user,
        sub_lesson=sublesson
    )

    progress.completed = not progress.completed
    progress.save()

    # Calcul de la progression
    total = sublesson.lesson.sub_lessons.count()
    completed = SubLessonProgress.objects.filter(
        student=user, 
        sub_lesson__lesson=sublesson.lesson, 
        completed=True
    ).count()

    return JsonResponse({
        'success': True,
        'completed': progress.completed,
        'completed_count': completed,
        'total_count': total,
        'progress_percent': int((completed / total) * 100)
    })
    
def certificates(request):
    speciality_id = request.GET.get('speciality')
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    certificates = Certificate.objects.all()

    if speciality_id:
        certificates = certificates.filter(speciality_id=speciality_id)

    if search_query:
        certificates = certificates.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Load all specialities
    specialities = Speciality.objects.all()

    # Link user attempts and count passed and total attempts
    user_attempts = {}
    passed_counts = {}
    total_attempts = {}
    if request.user.is_authenticated:
        attempts = CertificateAttempt.objects.filter(user=request.user).select_related('certificate')
        for attempt in attempts:
            cert_id = str(attempt.certificate_id)
            if cert_id not in user_attempts or attempt.completed_at > user_attempts[cert_id].completed_at:
                user_attempts[cert_id] = attempt
            # Count passed attempts per certificate
            if attempt.passed:
                if cert_id not in passed_counts:
                    passed_counts[cert_id] = 0
                passed_counts[cert_id] += 1
            # Count total attempts per certificate
            if cert_id not in total_attempts:
                total_attempts[cert_id] = 0
            total_attempts[cert_id] += 1

    # Filter by status (passed/failed) if specified before pagination
    if status_filter:
        cert_ids_with_attempts = set(user_attempts.keys())
        if status_filter == 'passed':
            cert_ids_to_include = {cert_id for cert_id, attempt in user_attempts.items() if attempt.passed}
        elif status_filter == 'failed':
            cert_ids_to_include = {cert_id for cert_id, attempt in user_attempts.items() if not attempt.passed}
        else:
            cert_ids_to_include = set()
        certificates = certificates.filter(id__in=cert_ids_to_include)

    # Get recommendations for logged-in user
    recommendations = []
    recommended_ids = []
    if request.user.is_authenticated:
        recommendations = get_recommendations(request.user.id)
        recommended_ids = [rec['id'] for rec in recommendations]

    # If no filters applied, show recommendations first
    if not speciality_id and not search_query and not status_filter:
        # Priority to recommendations, then other certificates
        recommended_certs = Certificate.objects.filter(id__in=recommended_ids)
        other_certs = certificates.exclude(id__in=recommended_ids)
        all_certs = list(recommended_certs) + list(other_certs)
    else:
        # If filters applied, use normal filtered list
        all_certs = list(certificates)

    # Pagination after all filters
    paginator = Paginator(all_certs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    certificates = page_obj.object_list

    # Attach user data to certificates and mark recommended
    for cert in certificates:
        cert.user_attempt = user_attempts.get(str(cert.id))
        cert.passed_count = passed_counts.get(str(cert.id), 0)
        cert.total_attempts = total_attempts.get(str(cert.id), 0)
        cert.is_recommended = cert.id in recommended_ids

    context = {
        'certificates': certificates,
        'page_obj': page_obj,
        'specialities': specialities,
        'selected_speciality': speciality_id,
        'search_query': search_query,
    }

    return render(request, 'certificates.html', context)

@login_required(login_url='login')
def take_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, pk=cert_id)
    exercises = CertificatExercise.objects.filter(certificate=certificate)

    if request.method == 'POST':
        # Create attempt
        attempt = CertificateAttempt.objects.create(
            user=request.user,
            certificate=certificate,
            total_questions=exercises.count()
        )

        score = 0
        for exercise in exercises:
            answer_key = f'answer_{exercise.id}'
            user_answer = request.POST.get(answer_key, '').strip()
            is_correct = False

            if exercise.exercise_type in ['truefalse', 'text']:
                is_correct = user_answer.lower() == exercise.correct_answer.lower()
            elif exercise.exercise_type == 'qcu':
                is_correct = user_answer == exercise.correct_answer

            if is_correct:
                score += 1

            CertificateAnswer.objects.create(
                attempt=attempt,
                exercise=exercise,
                answer=user_answer,
                is_correct=is_correct
            )

        attempt.score = score
        attempt.passed = score >= (exercises.count() * 0.7)
        attempt.save()

        # Prepare email
        user = request.user
        certificate_title = certificate.title
        score_percentage = int((score / exercises.count()) * 100)

        if attempt.passed:
            # Send certificate HTML
            context = {
                'name': user.username,
                'speciality': getattr(certificate.speciality, 'name', 'Non spécifiée'),
                'certificate_title': certificate.title,
            }
            html_content = render_to_string('certificateEmail.html', context)

            subject = f"🎉 Félicitations {user.username} ! Vous avez réussi le certificat {certificate_title}"
            text_content = (
                f"Félicitations {user.username} !\n\n"
                f"Vous avez réussi le certificat {certificate_title} avec un score de {score_percentage}%.\n"
                "Consultez votre certificat dans cet e-mail."
            )
        else:
            # Send motivational email
            subject = f"💪 Ne vous découragez pas {user.username} !"
            html_content = f"""
            <html>
            <body style="font-family:Arial,sans-serif; background:#f8f9fa; margin:0; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border-radius:12px;
                            box-shadow:0 4px 15px rgba(0,0,0,0.1); text-align:center;">
                    <img src="https://hubeducator-production.up.railway.app/static/website/img/favicons/android-chrome-192x192.png"
                         width="100" alt="HubEducator Logo" style="margin-bottom:20px;">
                    <h1 style="font-size:24px; margin:20px 0; color:#dc3545;">Ne vous découragez pas {user.username} !</h1>
                    <p style="font-size:16px;">Vous avez obtenu un score de {score_percentage}% pour le certificat <strong>{certificate_title}</strong>.</p>
                    <p style="font-size:16px;">Chaque échec est une opportunité d'apprendre. Essayez à nouveau pour réussir !</p>
                    <a href="{request.build_absolute_uri(f'/certificates/take/{cert_id}/')}"
                       style="display:inline-block; padding:12px 25px; color:#fff; background-color:#FFD700;
                              border-radius:8px; text-decoration:none; font-weight:600;">
                       Retenter le certificat
                    </a>
                </div>
            </body>
            </html>
            """
            text_content = (
                f"Ne vous découragez pas {user.username} !\n\n"
                f"Vous avez obtenu un score de {score_percentage}% pour le certificat {certificate_title}.\n"
                "Chaque échec est une opportunité d'apprendre. Essayez à nouveau pour réussir !"
            )

        # Send email
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return redirect('certificate_result', attempt_id=attempt.id)

    return render(request, 'take_certificate.html', {
        'certificate': certificate,
        'exercises': exercises,
    })

@login_required
def certificate_result(request, attempt_id):
    attempt = get_object_or_404(CertificateAttempt, pk=attempt_id, user=request.user)
    certificate = attempt.certificate
    attempts = CertificateAttempt.objects.filter(user=request.user, certificate=certificate).order_by('-completed_at')

    if request.GET.get('view') == 'certificate':
        context = {
            'name': request.user.username,
            'speciality': getattr(certificate.speciality, 'name', 'Non spécifiée'),
            'certificate_title': certificate.title,
        }
        return render(request, 'certificateTemplate.html', context)
    return render(request, 'certificate_result.html', {
        'certificate': certificate,
        'attempts': attempts,
    })

def certificate_detail(request, cert_id):
    certificate = get_object_or_404(Certificate, pk=cert_id)
    exercises = CertificatExercise.objects.filter(certificate=certificate)

    # Get user attempts for this certificate
    user_attempts = CertificateAttempt.objects.filter(user=request.user, certificate=certificate).order_by('-completed_at') if request.user.is_authenticated else []

    context = {
        'certificate': certificate,
        'exercises': exercises,
        'user_attempts': user_attempts,
    }

    return render(request, 'certificate_detail.html', context)

@login_required
def my_certificates(request):
    # Get all passed attempts for the current user
    passed_attempts = CertificateAttempt.objects.filter(
        user=request.user,
        passed=True
    ).select_related('certificate').order_by('-completed_at')

    context = {
        'passed_attempts': passed_attempts,
    }

    return render(request, 'my_certificates.html', context)

def get_recommendations(user_id):
    try:
        response = requests.get(f'http://127.0.0.1:5000/recommend/{user_id}')
        if response.status_code == 200:
            return response.json().get('recommendations', [])
        else:
            return []
    except requests.RequestException:
        return []

# Initialize OpenAI client only if API key is available
client = None
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
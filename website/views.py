from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from openai import OpenAI

from core.models import Certificate, Speciality, CertificatExercise, CertificateAttempt, CertificateAnswer
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

User = get_user_model()

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
# ----------------------------- Public Pages -----------------------------
def home(request):
    return render(request, 'home.html', {})

def pricing(request):
    return render(request, 'pricing.html', {})

def web_development(request):
    return render(request, 'web-development.html', {})

def user_research(request):
    return render(request, 'user-research.html', {})

def courseDetails(request):
    return render(request, 'courseDetails.html', {})

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
    return render(request, "login.html")


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
                    <img src="https://1cd2gyfjyi.ucarecd.net/b548c405-4541-4de3-97af-f3acc9ef1fad/logon.png" width="100" alt="HubEducator Logo" style="margin-bottom:20px;">
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


# views.py
import requests
from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login

User = get_user_model()

def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('/')  # Or some error page

    # Exchange the code for an access token
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

    # Get user info
    user_req = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        params={'access_token': access_token}
    )
    user_data = user_req.json()

    # Create or get user
    user, created = User.objects.get_or_create(email=user_data['email'])
    if created:
        user.username = user_data.get('name', user_data['email'])
        user.save()

    # Log the user in
    login(request, user)

    return redirect('/')  # Redirect to homepage after login


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

    # 🔹 Charger toutes les spécialités
    specialities = Speciality.objects.all()

    # 🔹 Lier les tentatives utilisateur et compter les passages réussis et totaux
    user_attempts = {}
    passed_counts = {}
    total_attempts = {}
    if request.user.is_authenticated:
        attempts = CertificateAttempt.objects.filter(user=request.user).select_related('certificate')
        for attempt in attempts:
            cert_id = str(attempt.certificate_id)
            if cert_id not in user_attempts or attempt.completed_at > user_attempts[cert_id].completed_at:
                user_attempts[cert_id] = attempt
            # Compter le nombre de passages réussis par certificat
            if attempt.passed:
                if cert_id not in passed_counts:
                    passed_counts[cert_id] = 0
                passed_counts[cert_id] += 1
            # Compter le nombre total de tentatives par certificat
            if cert_id not in total_attempts:
                total_attempts[cert_id] = 0
            total_attempts[cert_id] += 1

    # 🔹 Filtrer par status (passed/failed) si spécifié avant pagination
    if status_filter:
        cert_ids_with_attempts = set(user_attempts.keys())
        if status_filter == 'passed':
            cert_ids_to_include = {cert_id for cert_id, attempt in user_attempts.items() if attempt.passed}
        elif status_filter == 'failed':
            cert_ids_to_include = {cert_id for cert_id, attempt in user_attempts.items() if not attempt.passed}
        else:
            cert_ids_to_include = set()
        certificates = certificates.filter(id__in=cert_ids_to_include)

    # 🔹 Obtenir les recommandations pour l'utilisateur connecté
    recommendations = []
    recommended_ids = []
    if request.user.is_authenticated:
        recommendations = get_recommendations(request.user.id)
        recommended_ids = [rec['id'] for rec in recommendations]

    # 🔹 Si aucun filtre n'est appliqué, afficher les recommandations en premier
    if not speciality_id and not search_query and not status_filter:
        # Priorité aux recommandations, puis les autres certificats
        recommended_certs = Certificate.objects.filter(id__in=recommended_ids)
        other_certs = certificates.exclude(id__in=recommended_ids)
        all_certs = list(recommended_certs) + list(other_certs)
    else:
        # Si des filtres sont appliqués, utiliser la liste filtrée normale
        all_certs = list(certificates)

    # 🔹 Pagination après tous les filtres
    paginator = Paginator(all_certs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    certificates = page_obj.object_list

    # 🔹 Attacher les données utilisateur aux certificats et marquer les recommandés
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
    speciality_id = request.GET.get('speciality')
    search_query = request.GET.get('search', '').strip()

    certificates = Certificate.objects.all()

    if speciality_id:
        certificates = certificates.filter(speciality_id=speciality_id)

    if search_query:
        # Filtrage par recherche (titre ou description)
        certificates = certificates.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        # ⚠️ Désactiver la pagination si recherche
        page_obj = None
    else:
        # Pagination uniquement si pas de recherche
        paginator = Paginator(certificates, 12)  # 12 certificats par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        certificates = page_obj.object_list

    # Récupérer toutes les spécialités
    specialities = Speciality.objects.all()

    # Récupérer les tentatives utilisateur
    user_attempts = {}
    if request.user.is_authenticated:
        attempts = CertificateAttempt.objects.filter(user=request.user).select_related('certificate')
        for attempt in attempts:
            cert_id = str(attempt.certificate_id)
            if cert_id not in user_attempts or attempt.completed_at > user_attempts[cert_id].completed_at:
                user_attempts[cert_id] = attempt

    # Ajouter les tentatives à chaque certificat
    for cert in certificates:
        cert.user_attempt = user_attempts.get(str(cert.id))

    return render(request, 'certificates.html', {
        'certificates': certificates,
        'page_obj': page_obj,
        'specialities': specialities,
        'selected_speciality': speciality_id,
        'search_query': search_query,
    })
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

@login_required(login_url='login')
def take_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, pk=cert_id)
    exercises = CertificatExercise.objects.filter(certificate=certificate)

    if request.method == 'POST':
        # Création de la tentative
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

        # Préparation de l'email
        user = request.user
        certificate_title = certificate.title
        score_percentage = int((score / exercises.count()) * 100)

        if attempt.passed:
            # --- Envoi du certificat HTML ---
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
            # --- Envoi du mail de motivation ---
            subject = f"💪 Ne vous découragez pas {user.username} !"
            html_content = f"""
            <html>
            <body style="font-family:Arial,sans-serif; background:#f8f9fa; margin:0; padding:20px;">
                <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border-radius:12px;
                            box-shadow:0 4px 15px rgba(0,0,0,0.1); text-align:center;">
                    <img src="https://1cd2gyfjyi.ucarecd.net/b548c405-4541-4de3-97af-f3acc9ef1fad/logon.png"
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

        # Envoi du mail
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


    if request.method == "POST":
        user_input = request.POST.get("message")

        # Initialisation du client OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Appel à GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant utile."},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.choices[0].message.content
        return JsonResponse({"response": reply})

    return render(request, "chat.html")
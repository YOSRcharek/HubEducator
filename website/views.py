from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages

from core.models import User

# Create your views here.
def home (request):
    return render(request, 'home.html',{})

def pricing(request):
    return render(request, 'pricing.html',{}) 

def web_development(request):
    return render(request, 'web-development.html',{})

def user_research(request):
    return render(request, 'user-research.html',{})

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, "Connecté avec succès.")
                if user.role == 'admin':
                    return redirect('dashboard')
                elif user.role == 'teacher':
                    return redirect('dashboard')
                else: 
                    return redirect('home')
            else:
                messages.error(request, "Email ou mot de passe invalide.")
        except User.DoesNotExist:
            messages.error(request, "Aucun compte avec cet email.")
    return render(request, "login.html")

# LOGOUT
def logout_view(request):
    auth_logout(request)
    return redirect("login")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role", "student")

        if not username or not email or not password1:
            messages.error(request, "Remplis tous les champs requis.")
            return redirect("register")
        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect("register")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nom d'utilisateur déjà pris.")
            return redirect("register")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email déjà utilisé.")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.role = role
        # gérer upload d'image si présent
        if request.FILES.get("profile_picture"):
            user.profile_picture = request.FILES["profile_picture"]
        user.save()

        messages.success(request, "Compte créé — connecte-toi.")
        return redirect("login")
    return render(request, "register.html")

def courseDetails(request):
    return render(request, 'courseDetails.html',{})

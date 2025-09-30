from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm
from core.models import User
from core.decorators import unauthenticated_user

def home (request):
    return render(request, 'home.html',{})

def pricing(request):
    return render(request, 'pricing.html',{}) 

def web_development(request):
    return render(request, 'web-development.html',{})

def user_research(request):
    return render(request, 'user-research.html',{})

@unauthenticated_user
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
                if user.role == 'teacher':
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
            messages.success(request, "Compte créé — connecte-toi.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})

# LOGOUT
def logout_view(request):
    auth_logout(request)
    return redirect("login")


def courseDetails(request):
    return render(request, 'courseDetails.html',{})

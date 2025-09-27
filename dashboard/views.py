from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import AddUserForm, EditUserForm, EditUserForm
from core.models import User
from django.contrib import messages
from django.core.paginator import Paginator

@login_required
def dashboard(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))  # 'unauthorized' is the URL name
    return render(request, 'dashboard.html', {})

@login_required
def users(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    
    users_list = User.objects.exclude(role='admin')  # exclure admin si tu veux
    paginator = Paginator(users_list, 3)  # 5 utilisateurs par page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'users/users.html', {'page_obj': page_obj})

@login_required
def adduser(request):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))

    if request.method == "POST":
        form = AddUserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('users')  # après ajout, retour à la liste des users
    else:
        form = AddUserForm()

    return render(request, 'users/adduser.html', {'form': form})

@login_required
def edit_user(request, user_id):
    if request.user.role != "admin":
        return redirect(reverse("unauthorized"))

    user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = EditUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect("users")  # retourne vers la liste des users
    else:
        form = EditUserForm(instance=user)

    return render(request, "users/edituser.html", {"form": form, "user_obj": user})

@login_required
def delete_user(request, user_id):
    if request.user.role not in ['admin']:
        return redirect(reverse('unauthorized'))
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully!")
    return redirect('users')  

@login_required
def profil(request):
    return render(request, 'profil.html', {})

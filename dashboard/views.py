from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import AddUserForm, EditUserForm, SubscriptionForm
from core.models import User, Subscription, UserSubscription, Transaction
from django.contrib import messages
from django.core.paginator import Paginator
from core.forms import ProfileUpdateForm
from django.contrib.auth import get_user_model
@login_required
def dashboard(request):
    if request.user.role not in ['admin']:
        return redirect(reverse('unauthorized'))  # 'unauthorized' is the URL name
    return render(request, 'dashboard.html', {})

@login_required
def users(request):
    if request.user.role not in ['admin']:
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


# --------------------------
# Subscriptions Management (CRUD)
# --------------------------

@login_required
def subscriptions(request):
    """List all subscriptions separated by type"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    # Get student subscriptions
    student_subscriptions = Subscription.objects.filter(user_type='student').order_by('-created_at')
    
    # Get teacher subscriptions
    teacher_subscriptions = Subscription.objects.filter(user_type='teacher').order_by('-created_at')
    
    # Pagination for student subscriptions
    student_paginator = Paginator(student_subscriptions, 3)
    student_page_number = request.GET.get('student_page')
    student_page_obj = student_paginator.get_page(student_page_number)
    
    # Pagination for teacher subscriptions
    teacher_paginator = Paginator(teacher_subscriptions, 3)
    teacher_page_number = request.GET.get('teacher_page')
    teacher_page_obj = teacher_paginator.get_page(teacher_page_number)
    
    return render(request, 'subscriptions/subscriptions.html', {
        'student_page_obj': student_page_obj,
        'teacher_page_obj': teacher_page_obj,
    })


@login_required
def student_subscriptions(request):
    """List student subscriptions with pagination"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    subscriptions_list = Subscription.objects.filter(user_type='student').order_by('-created_at')
    
    # Pagination: 10 subscriptions per page
    paginator = Paginator(subscriptions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'subscriptions/student_subscriptions.html', {
        'page_obj': page_obj,
        'subscription_type': 'Student'
    })


@login_required
def teacher_subscriptions(request):
    """List teacher subscriptions with pagination"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    subscriptions_list = Subscription.objects.filter(user_type='teacher').order_by('-created_at')
    
    # Pagination: 10 subscriptions per page
    paginator = Paginator(subscriptions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'subscriptions/teacher_subscriptions.html', {
        'page_obj': page_obj,
        'subscription_type': 'Teacher'
    })


@login_required
def add_subscription(request):
    """Add a new subscription"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription added successfully!")
            return redirect('subscriptions')
    else:
        form = SubscriptionForm()
    
    return render(request, 'subscriptions/add_subscription.html', {'form': form})


@login_required
def edit_subscription(request, subscription_id):
    """Edit an existing subscription"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    
    if request.method == "POST":
        form = SubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription updated successfully!")
            return redirect('subscriptions')
    else:
        form = SubscriptionForm(instance=subscription)
    
    return render(request, 'subscriptions/edit_subscription.html', {
        'form': form,
        'subscription': subscription
    })


@login_required
def delete_subscription(request, subscription_id):
    """Delete a subscription"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    subscription.delete()
    messages.success(request, "Subscription deleted successfully!")
    return redirect('subscriptions')


@login_required
def subscription_detail(request, subscription_id):
    """View subscription details"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    
    return render(request, 'subscriptions/subscription_detail.html', {
        'subscription': subscription
    })


@login_required
def user_subscriptions(request):
    """List all user subscriptions"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    # Get all user subscriptions
    user_subscriptions_list = UserSubscription.objects.all().select_related('user', 'subscription', 'transaction').order_by('-created_at')
    
    # Pagination: 6 user subscriptions per page
    paginator = Paginator(user_subscriptions_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'user_subscriptions/user_subscriptions.html', {
        'page_obj': page_obj
    })


@login_required
def delete_user_subscription(request, subscription_id):
    """Delete a user subscription"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    user_subscription = get_object_or_404(UserSubscription, id=subscription_id)
    username = user_subscription.user.username
    
    user_subscription.delete()
    messages.success(request, f'Subscription for {username} has been deleted successfully.')
    
    return redirect('user_subscriptions')


@login_required
def transactions(request):
    """List all transactions"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    # Get all transactions
    transactions_list = Transaction.objects.all().select_related('user', 'subscription').order_by('-created_at')
    
    # Pagination: 10 transactions per page
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'transactions/transactions.html', {
        'page_obj': page_obj
    })


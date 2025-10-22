
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from .forms import EmailForm, ProfileUpdateForm, PasswordForm
from .models import UserSubscription, Transaction


def unauthorized (request):
    return render(request, 'unauthorized.html',{})

User = get_user_model()
@login_required
def profil(request):
    user = request.user

    profile_form = ProfileUpdateForm(instance=user)
    email_form = EmailForm(user=user)
    password_form = PasswordForm(user=user)

    show_email_success = False
    show_email_error = None
    show_password_success = False
    show_password_error = None
    show_deactivate_success = False
    show_deactivate_error = None

    if request.method == "POST":

        # --- Profile update ---
        if "update_profile" in request.POST:
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            avatar_remove = request.POST.get("avatar_remove", "")
            if profile_form.is_valid():
                user = profile_form.save(commit=False)
                if avatar_remove in ["1", "true", "on"] and user.profile_picture:
                    user.profile_picture.delete(save=False)
                    user.profile_picture = None
                user.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("profil")

        # --- Email update ---
        elif "update_email" in request.POST:
            email_form = EmailForm(request.POST, user=user)
            if email_form.is_valid():
                new_email = email_form.cleaned_data["email"]
                if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                    show_email_error = "This email is already taken."
                else:
                    user.email = new_email
                    user.save()
                    logout(request)
                    show_email_success = True
            else:
                errors = email_form.non_field_errors()
                show_email_error = errors[0] if errors else "Please correct the errors in the email form."

        # --- Password update ---
        elif "update_password" in request.POST:
            password_form = PasswordForm(request.POST, user=user)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data["new_password"])
                user.save()
                logout(request)
                show_password_success = True
            else:
                errors = password_form.non_field_errors()
                show_password_error = errors[0] if errors else "Please correct the errors in the password form."
                
        # --- Deactivate account ---
        elif "deactivate_account" in request.POST:
            if "deactivate" in request.POST:  # checkbox is checked
                user = request.user  # current user instance
                user.is_active = False
                user.save(update_fields=['is_active'])  # update DB
                show_deactivate_success = True
                messages.success(request, "Your account has been deactivated.")
                #logout(request)
                #return redirect("login")  # redirect to login page
            else:
                show_deactivate_error = "You must confirm account deactivation."

    return render(request, "profil.html", {
        "profile_form": profile_form,
        "email_form": email_form,
        "password_form": password_form,
        "user": user,
        "show_email_success": show_email_success,
        "show_email_error": show_email_error,
        "show_password_success": show_password_success,
        "show_password_error": show_password_error,
        "show_deactivate_success": show_deactivate_success,
        "show_deactivate_error": show_deactivate_error,
    })


@login_required
def my_subscription_teacher(request):
    """View for teachers to see their current subscription"""
    if request.user.role != 'teacher':
        return redirect('unauthorized')
    
    # Get the active subscription for this teacher
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subscription').first()
    
    return render(request, 'my_subscription_teacher.html', {
        'user_subscription': active_subscription,
        'user_type': 'teacher'
    })


@login_required
def my_subscription_student(request):
    """View for students to see their current subscription"""
    if request.user.role != 'student':
        return redirect('unauthorized')
    
    # Get the active subscription for this student
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subscription').first()
    
    return render(request, 'my_subscription_student.html', {
        'user_subscription': active_subscription,
        'user_type': 'student'
    })


@login_required
def payment_history_teacher(request):
    """View for teachers to see their payment history"""
    if request.user.role != 'teacher':
        return redirect('unauthorized')
    
    # Get all transactions for this teacher
    transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('subscription').order_by('-created_at')
    
    # Calculate total spent (only completed transactions)
    total_spent = sum(t.amount for t in transactions if t.status == 'completed')
    
    return render(request, 'payment_history_teacher.html', {
        'transactions': transactions,
        'total_spent': total_spent,
        'user_type': 'teacher'
    })


@login_required
def payment_history_student(request):
    """View for students to see their payment history"""
    if request.user.role != 'student':
        return redirect('unauthorized')
    
    # Get all transactions for this student
    transactions = Transaction.objects.filter(
        user=request.user
    ).select_related('subscription').order_by('-created_at')
    
    # Calculate total spent (only completed transactions)
    total_spent = sum(t.amount for t in transactions if t.status == 'completed')
    
    return render(request, 'payment_history_student.html', {
        'transactions': transactions,
        'total_spent': total_spent,
        'user_type': 'student'
    })

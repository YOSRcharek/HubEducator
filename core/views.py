
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.http import HttpResponse
from .forms import EmailForm, ProfileUpdateForm, PasswordForm
from .models import UserSubscription, Transaction, Subscription
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.http import HttpResponse
from .forms import EmailForm, ProfileUpdateForm, PasswordForm
from .models import UserSubscription, Transaction, Subscription
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime



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
    
    # Get all available teacher subscriptions
    available_subscriptions = Subscription.objects.filter(
        user_type='teacher',
        is_active=True
    ).order_by('price')
    
    return render(request, 'my_subscription_teacher.html', {
        'user_subscription': active_subscription,
        'user_type': 'teacher',
        'available_subscriptions': available_subscriptions
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
    
    # Get all available student subscriptions
    available_subscriptions = Subscription.objects.filter(
        user_type='student',
        is_active=True
    ).order_by('price')
    
    return render(request, 'my_subscription_student.html', {
        'user_subscription': active_subscription,
        'user_type': 'student',
        'available_subscriptions': available_subscriptions
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


@login_required
def change_subscription_teacher(request):
    """View for teachers to browse and change their subscription"""
    if request.user.role != 'teacher':
        return redirect('unauthorized')
    
    # Delete old preferences to force new questionnaire
    try:
        from .ml_models import UserPreference
        UserPreference.objects.filter(user=request.user).delete()
    except Exception as e:
        print(f"Error deleting old preferences: {e}")
    
    # Get the active subscription for this teacher
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subscription').first()
    
    # Get all available teacher subscriptions
    available_subscriptions = Subscription.objects.filter(
        user_type='teacher',
        is_active=True
    ).order_by('price')
    
    # No AI recommendations - user must complete questionnaire
    ai_recommendations = None
    
    return render(request, 'change_subscription_teacher.html', {
        'user_subscription': active_subscription,
        'available_subscriptions': available_subscriptions,
        'user_type': 'teacher',
        'ai_recommendations': ai_recommendations
    })


@login_required
def change_subscription_student(request):
    """View for students to browse and change their subscription"""
    if request.user.role != 'student':
        return redirect('unauthorized')
    
    # Delete old preferences to force new questionnaire
    try:
        from .ml_models import UserPreference
        UserPreference.objects.filter(user=request.user).delete()
    except Exception as e:
        print(f"Error deleting old preferences: {e}")
    
    # Get the active subscription for this student
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('subscription').first()
    
    # Get all available student subscriptions
    available_subscriptions = Subscription.objects.filter(
        user_type='student',
        is_active=True
    ).order_by('price')
    
    # No AI recommendations - user must complete questionnaire
    ai_recommendations = None
    
    return render(request, 'change_subscription_student.html', {
        'user_subscription': active_subscription,
        'available_subscriptions': available_subscriptions,
        'user_type': 'student',
        'ai_recommendations': ai_recommendations
    })


@login_required
def unsubscribe(request):
    """Unsubscribe user from their current active subscription"""
    if request.user.role not in ['student', 'teacher']:
        return redirect('unauthorized')
    
    # Get the active subscription for this user
    active_subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if active_subscription:
        # Deactivate the subscription
        active_subscription.is_active = False
        active_subscription.save()
    
    # Redirect based on user type with a timestamp to force reload
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    
    if request.user.role == 'teacher':
        url = reverse('my_subscription_teacher')
    else:
        url = reverse('my_subscription_student')
    
    return HttpResponseRedirect(url)


@login_required
def download_invoice(request, transaction_id):
    """Generate and download PDF invoice for a transaction"""
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="HubEducator_Invoice_{transaction.id}.pdf"'
    
    # Create the PDF object using BytesIO as a buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=30, bottomMargin=30)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Header with colored background
    header_data = [[Paragraph('<font size="28" color="white"><b>INVOICE</b></font>', styles['Normal'])]]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#667eea')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', [10, 10, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Company and Invoice Info in two columns
    company_bill_data = [
        [
            Paragraph('<font size="11"><b>FROM:</b></font><br/><font size="10"><b>HubEducator</b><br/>La petite Ariana, Ariana 2080<br/>contact@hubeducator.com</font>', styles['Normal']),
            Paragraph(f'<font size="11"><b>BILL TO:</b></font><br/><font size="10"><b>{transaction.user.first_name} {transaction.user.last_name}</b><br/>{transaction.user.email}</font>', styles['Normal'])
        ]
    ]
    company_bill_table = Table(company_bill_data, colWidths=[3.5*inch, 3.5*inch])
    company_bill_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(company_bill_table)
    elements.append(Spacer(1, 25))
    
    # Invoice details box with modern design
    status_color = '#48bb78' if transaction.status == 'completed' else '#f6ad55'
    invoice_details_data = [
        [
            Paragraph('<font size="9" color="#718096"><b>INVOICE NUMBER</b></font>', styles['Normal']),
            Paragraph('<font size="9" color="#718096"><b>DATE</b></font>', styles['Normal']),
            Paragraph('<font size="9" color="#718096"><b>STATUS</b></font>', styles['Normal']),
        ],
        [
            Paragraph(f'<font size="11"><b>INV-{str(transaction.id).zfill(6)}</b></font>', styles['Normal']),
            Paragraph(f'<font size="11">{transaction.created_at.strftime("%d %B %Y")}</font>', styles['Normal']),
            Paragraph(f'<font size="11" color="{status_color}"><b>{transaction.status.upper()}</b></font>', styles['Normal']),
        ]
    ]
    invoice_details_table = Table(invoice_details_data, colWidths=[2.33*inch, 2.33*inch, 2.34*inch])
    invoice_details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7fafc')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(invoice_details_table)
    elements.append(Spacer(1, 30))
    
    # Items table with modern design
    items_header = [
        Paragraph('<font size="10" color="white"><b>DESCRIPTION</b></font>', styles['Normal']),
        Paragraph('<font size="10" color="white"><b>DURATION</b></font>', styles['Normal']),
        Paragraph('<font size="10" color="white"><b>AMOUNT</b></font>', styles['Normal'])
    ]
    
    items_row = [
        Paragraph(f'<font size="10">{transaction.subscription.name if transaction.subscription else "N/A"}</font>', styles['Normal']),
        Paragraph(f'<font size="10">{transaction.subscription.duration if transaction.subscription else "N/A"}</font>', styles['Normal']),
        Paragraph(f'<font size="10"><b>{transaction.currency.upper()} {transaction.amount}</b></font>', styles['Normal'])
    ]
    
    items_data = [items_header, items_row]
    items_table = Table(items_data, colWidths=[3.5*inch, 2*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#e2e8f0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 25))
    
    # Total section with modern design
    total_data = [
        [Paragraph('<font size="10">Subtotal:</font>', styles['Normal']), Paragraph(f'<font size="10">{transaction.currency.upper()} {transaction.amount}</font>', styles['Normal'])],
        [Paragraph('<font size="10">Tax (0%):</font>', styles['Normal']), Paragraph(f'<font size="10">{transaction.currency.upper()} 0.00</font>', styles['Normal'])],
        [Paragraph('<font size="12" color="#667eea"><b>TOTAL:</b></font>', styles['Normal']), Paragraph(f'<font size="14" color="#667eea"><b>{transaction.currency.upper()} {transaction.amount}</b></font>', styles['Normal'])],
    ]
    
    total_table = Table(total_data, colWidths=[5.5*inch, 1.5*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#667eea')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f7fafc')),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 40))
    
    # Footer with modern design
    footer_data = [[
        Paragraph('<font size="10" color="#667eea"><b>Thank you for your business!</b></font><br/><font size="8" color="#718096">If you have any questions about this invoice, please contact us at contact@hubeducator.com<br/>This is a computer-generated invoice and does not require a signature.</font>', styles['Normal'])
    ]]
    footer_table = Table(footer_data, colWidths=[7*inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

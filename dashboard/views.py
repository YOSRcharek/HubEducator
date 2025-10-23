from django.db.models import Count, Q
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import AddUserForm, EditUserForm, EditUserForm
from core.models import CertificateAttempt, User
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib import messages
from core.forms import ProfileUpdateForm
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from core.models import Speciality
from .forms import SpecialityForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from core.models import CertificatExercise, Certificate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import Certificate, CertificatExercise, Speciality
from .forms import CertificateForm, CertificatExerciseForm
from django.forms import modelformset_factory
from django.db import transaction
import csv
from django.http import HttpResponse
from openpyxl import Workbook
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from .forms import AddUserForm, EditUserForm, SubscriptionForm
from core.models import User, Subscription, UserSubscription, Transaction
from django.contrib import messages
from django.core.paginator import Paginator
from core.forms import ProfileUpdateForm
from django.contrib.auth import get_user_model
from core.ml.models.churn_predictor import ChurnPredictor
from core.ml.models.revenue_forecaster import RevenueForecaster
from core.ml.models.ltv_calculator import LTVCalculator
import json
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


@method_decorator(login_required, name='dispatch')
class SpecialityListView(View):
    def get(self, request):
        specialities = Speciality.objects.all()
        return render(request, 'specialities/listSpecialities.html', {'specialities': specialities})

@method_decorator(login_required, name='dispatch')
class SpecialityCreateView(View):
    def get(self, request):
        form = SpecialityForm()
        return render(request, 'specialities/addSpecialities.html', {'form': form})

    def post(self, request):
        form = SpecialityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('specialities')  # corriger nom url
        return render(request, 'specialities/addSpecialities.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class SpecialityUpdateView(View):
    def get(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        form = SpecialityForm(instance=speciality)
        return render(request, 'specialities/editSpecialities.html', {'form': form})

    def post(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        form = SpecialityForm(request.POST, instance=speciality)
        if form.is_valid():
            form.save()
            return redirect('specialities')
        return render(request, 'specialities/editSpecialities.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class SpecialityDeleteView(View):
    def post(self, request, speciality_id):
        speciality = get_object_or_404(Speciality, pk=speciality_id)
        speciality.delete()
        return redirect('specialities')

class ListCertificatView(View):
    def get(self, request):
        search_query = request.GET.get('search', '')
        certificates_qs = Certificate.objects.annotate(
            exercise_count=Count('exercises'),
            participant_count=Count('certificateattempt', distinct=True),
            succeeded_count=Count('certificateattempt', filter=Q(certificateattempt__passed=True), distinct=True)
        ).all().order_by('id')

        if search_query:
            certificates_qs = certificates_qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(speciality__name__icontains=search_query)
            )

        if search_query:
            certificates = certificates_qs
            page_obj = None
        else:
            paginator = Paginator(certificates_qs, 10)  # 10 items per page
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            certificates = page_obj.object_list

        return render(request, 'certificats/listCertificate.html', {
            'certificates': certificates,
            'page_obj': page_obj,
            'search_query': search_query
        })


@login_required
def create_certificate(request):
    CertificatExerciseFormSet = modelformset_factory(
        CertificatExercise,
        form=CertificatExerciseForm,
        extra=1,  # une ligne vide par défaut
        can_delete=True
    )

    exercise_error = None

    if request.method == 'POST':
        cert_form = CertificateForm(request.POST, request.FILES)
        formset = CertificatExerciseFormSet(
            request.POST,
            queryset=CertificatExercise.objects.none(),
            prefix='exercise'
        )

        if cert_form.is_valid() and formset.is_valid():
            exercises_to_save = []
            has_empty_exercise = False

            for form in formset:
                if not form.cleaned_data.get('DELETE'):
                    exercise_type = form.cleaned_data.get('exercise_type')
                    has_data = (
                        form.cleaned_data.get('question') or
                        form.cleaned_data.get('option1') or
                        form.cleaned_data.get('option2') or
                        form.cleaned_data.get('option3') or
                        form.cleaned_data.get('option4')
                    )
                    if has_data and not exercise_type:
                        has_empty_exercise = True
                        break
                    elif exercise_type:
                        exercises_to_save.append(form)

            if has_empty_exercise:
                exercise_error = "All exercises must have an exercise type selected."
            elif not exercises_to_save:
                exercise_error = "At least one exercise is required."
            else:
                certificate = cert_form.save(commit=False)
                certificate.save()
                for form in exercises_to_save:
                    exercise = form.save(commit=False)
                    exercise.certificate = certificate
                    exercise.save()
                messages.success(request, "Certificate created successfully!")
                return redirect('list_certificates')
        else:
            exercise_error = "Please correct the errors in the exercises."
    else:
        cert_form = CertificateForm()
        formset = CertificatExerciseFormSet(
            queryset=CertificatExercise.objects.none(),
            prefix='exercise'
        )

    specialities = Speciality.objects.all()
    return render(request, 'certificats/certificate_form.html', {
        'cert_form': cert_form,
        'formset': formset,
        'exercise_error': exercise_error,
        'specialities': specialities,
    })


# AJOUT / MODIF: edit_certificate (passer et traiter formset avec exercises existants)
@login_required
def edit_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, pk=cert_id)
    CertificatExerciseFormSet = modelformset_factory(
        CertificatExercise,
        form=CertificatExerciseForm,
        extra=0,  # pas de formulaire vide automatiquement
        can_delete=True
    )

    exercise_error = None

    if request.method == "POST":
        cert_form = CertificateForm(request.POST, request.FILES, instance=certificate)
        formset = CertificatExerciseFormSet(
            request.POST,
            queryset=CertificatExercise.objects.filter(certificate=certificate),
            prefix='exercise'
        )

        if cert_form.is_valid() and formset.is_valid():
            exercises_to_save = []
            has_empty_exercise = False

            for form in formset:
                if not form.cleaned_data.get('DELETE'):
                    exercise_type = form.cleaned_data.get('exercise_type')
                    has_data = (
                        form.cleaned_data.get('question') or
                        form.cleaned_data.get('option1') or
                        form.cleaned_data.get('option2') or
                        form.cleaned_data.get('option3') or
                        form.cleaned_data.get('option4')
                    )
                    if has_data and not exercise_type:
                        has_empty_exercise = True
                        break
                    elif exercise_type:
                        exercises_to_save.append(form)

            if has_empty_exercise:
                exercise_error = "All exercises must have an exercise type selected."
            elif not exercises_to_save:
                exercise_error = "At least one exercise is required."
            else:
                try:
                    with transaction.atomic():
                        cert_form.save()
                        for form in formset.forms:
                            if form.cleaned_data.get('DELETE') and form.instance.pk:
                                form.instance.delete()
                            elif form.cleaned_data.get('exercise_type'):
                                exercise = form.save(commit=False)
                                exercise.certificate = certificate
                                exercise.save()
                        messages.success(request, "Certificate updated successfully!")
                        return redirect('list_certificates')
                except Exception as e:
                    messages.error(request, f"Error updating certificate: {str(e)}")
        else:
            exercise_error = "Please correct the errors in the exercises."
    else:
        cert_form = CertificateForm(instance=certificate)
        formset = CertificatExerciseFormSet(
            queryset=CertificatExercise.objects.filter(certificate=certificate),
            prefix='exercise'
        )

    return render(request, 'certificats/editCertificate.html', {
        'cert_form': cert_form,
        'formset': formset,
        'certificate': certificate,
        'exercise_error': exercise_error,
    })

# AJOUT: delete_certificate
@login_required
def delete_certificate(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    if request.method == "POST":
        certificate.delete()
        messages.success(request, "Certificate deleted successfully.")
        return redirect('list_certificates')
    # If not POST, redirect back to list
    return redirect('list_certificates')

@login_required
def preview_certificate(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    exercises = CertificatExercise.objects.filter(certificate=certificate)
    return render(request, 'certificats/preview_certificate.html', {
        'certificate': certificate,
        'exercises': exercises,
    })

@login_required
def certificate_results(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    attempts = CertificateAttempt.objects.filter(certificate=certificate).select_related('user').order_by('-completed_at')
    return render(request, 'certificats/certificate_results.html', {
        'certificate': certificate,
        'attempts': attempts,
    })

@login_required
def attempt_details(request, attempt_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    attempt = get_object_or_404(CertificateAttempt, pk=attempt_id)
    answers = attempt.answers.select_related('exercise').all()
    return render(request, 'certificats/attempt_details.html', {
        'attempt': attempt,
        'answers': answers,
    })

@login_required
def export_certificate_results_csv(request, cert_id):
    if request.user.role not in ['admin', 'teacher']:
        return redirect(reverse('unauthorized'))
    certificate = get_object_or_404(Certificate, pk=cert_id)
    attempts = CertificateAttempt.objects.filter(certificate=certificate).select_related('user').prefetch_related('answers__exercise').order_by('-completed_at')

    # Get all exercises for this certificate
    exercises = list(CertificatExercise.objects.filter(certificate=certificate).order_by('id'))

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Certificate Results"

    # Write headers
    headers = ['User', 'Score', 'Total Questions', 'Passed', 'Completed At']
    for exercise in exercises:
        headers.append(f"{exercise.question} - Answer")
        headers.append(f"{exercise.question} - Correct Answer")

    for col_num, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_num, value=header)

    # Write data
    for row_num, attempt in enumerate(attempts, 2):
        ws.cell(row=row_num, column=1, value=attempt.user.username)
        ws.cell(row=row_num, column=2, value=attempt.score)
        ws.cell(row=row_num, column=3, value=attempt.total_questions)
        ws.cell(row=row_num, column=4, value='Yes' if attempt.passed else 'No')
        ws.cell(row=row_num, column=5, value=attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S'))

        # Create a dict of exercise_id to answer for quick lookup
        answers_dict = {answer.exercise_id: answer for answer in attempt.answers.all()}

        col_num = 6
        for exercise in exercises:
            if exercise.id in answers_dict:
                answer = answers_dict[exercise.id]
                ws.cell(row=row_num, column=col_num, value=answer.answer)
                ws.cell(row=row_num, column=col_num + 1, value=exercise.correct_answer)
            else:
                ws.cell(row=row_num, column=col_num, value='')
                ws.cell(row=row_num, column=col_num + 1, value=exercise.correct_answer)
            col_num += 2

    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{certificate.title}_results.xlsx"'

    wb.save(response)
    return response
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
    
    # Get filter parameter from URL
    user_type = request.GET.get('type', 'all')
    
    # Get all user subscriptions with optional filtering
    user_subscriptions_list = UserSubscription.objects.all().select_related('user', 'subscription', 'transaction')
    
    # Apply filter based on user type
    if user_type == 'student':
        user_subscriptions_list = user_subscriptions_list.filter(user__role='student')
    elif user_type == 'teacher':
        user_subscriptions_list = user_subscriptions_list.filter(user__role='teacher')
    
    user_subscriptions_list = user_subscriptions_list.order_by('-created_at')
    
    # Pagination: 6 user subscriptions per page
    paginator = Paginator(user_subscriptions_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'user_subscriptions/user_subscriptions.html', {
        'page_obj': page_obj,
        'current_filter': user_type
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
    
    # Pagination: 6 transactions per page
    paginator = Paginator(transactions_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'transactions/transactions.html', {
        'page_obj': page_obj
    })


# --------------------------
# ML Analytics Views
# --------------------------

@login_required
def ml_insights(request):
    """ML insights dashboard with predictions and analytics"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    # Get basic statistics
    total_subscriptions = UserSubscription.objects.filter(is_active=True).count()
    total_revenue = Transaction.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Monthly revenue trend
    monthly_revenue = Transaction.objects.filter(
        status='completed'
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('amount')
    ).order_by('month')[:12]
    
    context = {
        'total_subscriptions': total_subscriptions,
        'total_revenue': total_revenue,
        'monthly_revenue': list(monthly_revenue),
    }
    
    return render(request, 'ml_insights/dashboard.html', context)


@login_required
def churn_predictions(request):
    """View churn predictions for all active subscriptions"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    try:
        # Load predictor
        predictor = ChurnPredictor()
        predictor.load()
        
        # Get active subscriptions
        subscriptions = UserSubscription.objects.filter(
            is_active=True
        ).select_related('user', 'subscription')
        
        # Generate predictions
        predictions = predictor.predict_batch(subscriptions)
        
        # Sort by churn probability
        predictions.sort(key=lambda x: x['churn_probability'], reverse=True)
        
        # Add subscription details
        for pred in predictions:
            subscription = UserSubscription.objects.select_related('user', 'subscription').get(id=pred['subscription_id'])
            pred['username'] = subscription.user.username
            pred['email'] = subscription.user.email
            pred['plan'] = subscription.subscription.user_type
            pred['amount'] = float(subscription.subscription.price)
        
        # Count by risk level
        risk_counts = {
            'high': len([p for p in predictions if p['risk_level'] == 'high']),
            'medium': len([p for p in predictions if p['risk_level'] == 'medium']),
            'low': len([p for p in predictions if p['risk_level'] == 'low']),
        }
        
        # Pagination
        paginator = Paginator(predictions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'risk_counts': risk_counts,
            'total_predictions': len(predictions),
            'model_info': predictor.get_model_info(),
        }
        
        return render(request, 'ml_insights/churn_predictions.html', context)
    
    except FileNotFoundError:
        messages.error(request, 'Churn model not trained yet. Please train the model first.')
        return redirect('ml_insights')
    except Exception as e:
        messages.error(request, f'Error generating predictions: {str(e)}')
        return redirect('ml_insights')


@login_required
def revenue_forecast(request):
    """View revenue forecasts"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    try:
        # Load forecaster
        forecaster = RevenueForecaster()
        forecaster.load()
        
        # Get forecasts for next 6 periods
        forecasts = forecaster.forecast(periods_ahead=6)
        
        # Get revenue insights
        insights = forecaster.get_revenue_insights()
        
        # Get historical data for chart
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        monthly_revenue = Transaction.objects.filter(
            status='completed'
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount')
        ).order_by('month')
        
        historical_data = [
            {
                'date': item['month'].strftime('%Y-%m'),
                'revenue': float(item['revenue'])
            }
            for item in monthly_revenue
        ]
        
        # Create forecast data
        if historical_data:
            last_date = datetime.strptime(historical_data[-1]['date'], '%Y-%m')
        else:
            last_date = timezone.now()
        
        forecast_data = []
        for i, forecast in enumerate(forecasts, 1):
            next_month = last_date + timedelta(days=30 * i)
            forecast_data.append({
                'date': next_month.strftime('%Y-%m'),
                'revenue': forecast
            })
        
        context = {
            'forecasts': forecast_data,
            'insights': insights,
            'historical_data': historical_data,
            'model_info': forecaster.metadata,
        }
        
        return render(request, 'ml_insights/revenue_forecast.html', context)
    
    except FileNotFoundError:
        messages.error(request, 'Revenue model not trained yet. Please train the model first.')
        return redirect('ml_insights')
    except Exception as e:
        messages.error(request, f'Error generating forecast: {str(e)}')
        return redirect('ml_insights')


@login_required
def ltv_analysis(request):
    """View LTV analysis for users"""
    if request.user.role != 'admin':
        return redirect(reverse('unauthorized'))
    
    try:
        # Load calculator
        calculator = LTVCalculator()
        calculator.load()
        
        # Get active subscriptions
        subscriptions = UserSubscription.objects.filter(
            is_active=True
        ).select_related('user', 'subscription')
        
        # Generate LTV predictions
        predictions = []
        for subscription in subscriptions:
            try:
                pred = calculator.predict_ltv(subscription)
                pred['username'] = subscription.user.username
                pred['email'] = subscription.user.email
                pred['plan'] = subscription.subscription.user_type
                predictions.append(pred)
            except Exception as e:
                print(f"Error predicting LTV for {subscription.id}: {e}")
        
        # Sort by predicted LTV
        predictions.sort(key=lambda x: x['predicted_ltv'], reverse=True)
        
        # Calculate statistics
        if predictions:
            total_current_ltv = sum(p['current_ltv'] for p in predictions)
            total_predicted_ltv = sum(p['predicted_ltv'] for p in predictions)
            total_potential = sum(p['ltv_potential'] for p in predictions)
            avg_current_ltv = total_current_ltv / len(predictions)
            avg_predicted_ltv = total_predicted_ltv / len(predictions)
        else:
            total_current_ltv = total_predicted_ltv = total_potential = 0
            avg_current_ltv = avg_predicted_ltv = 0
        
        # Get LTV segments
        segments = calculator.get_ltv_segments()
        
        # Pagination
        paginator = Paginator(predictions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'total_current_ltv': total_current_ltv,
            'total_predicted_ltv': total_predicted_ltv,
            'total_potential': total_potential,
            'avg_current_ltv': avg_current_ltv,
            'avg_predicted_ltv': avg_predicted_ltv,
            'segments': segments,
            'model_info': calculator.metadata,
        }
        
        return render(request, 'ml_insights/ltv_analysis.html', context)
    
    except FileNotFoundError:
        messages.error(request, 'LTV model not trained yet. Please train the model first.')
        return redirect('ml_insights')
    except Exception as e:
        messages.error(request, f'Error generating LTV analysis: {str(e)}')
        return redirect('ml_insights')


# --------------------------
# ML API Endpoints (JSON)
# --------------------------

@login_required
def api_predict_churn(request, subscription_id):
    """API endpoint to predict churn for a specific subscription"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        subscription = get_object_or_404(UserSubscription, id=subscription_id)
        
        predictor = ChurnPredictor()
        predictor.load()
        
        prediction = predictor.predict(subscription)
        
        return JsonResponse(prediction)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_revenue_forecast(request):
    """API endpoint to get revenue forecast"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        periods = int(request.GET.get('periods', 3))
        
        forecaster = RevenueForecaster()
        forecaster.load()
        
        forecasts = forecaster.forecast(periods_ahead=periods)
        insights = forecaster.get_revenue_insights()
        
        return JsonResponse({
            'forecasts': forecasts,
            'insights': insights
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_ltv_prediction(request, subscription_id):
    """API endpoint to predict LTV for a specific subscription"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        subscription = get_object_or_404(UserSubscription, id=subscription_id)
        
        calculator = LTVCalculator()
        calculator.load()
        
        prediction = calculator.predict_ltv(subscription)
        
        return JsonResponse(prediction)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


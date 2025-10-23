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


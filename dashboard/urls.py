

from django.urls import path
from . import views
from core import views as core_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profil/', core_views.profil, name='profil'),
    path('users/', views.users, name='users'),
    path('users/add', views.adduser, name='adduser'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edituser'),
    path('users/delete/<int:user_id>/', views.delete_user, name='deleteuser'),
    
    # Subscriptions URLs
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('subscriptions/students/', views.student_subscriptions, name='student_subscriptions'),
    path('subscriptions/teachers/', views.teacher_subscriptions, name='teacher_subscriptions'),
    path('subscriptions/add/', views.add_subscription, name='add_subscription'),
    path('subscriptions/edit/<int:subscription_id>/', views.edit_subscription, name='edit_subscription'),
    path('subscriptions/delete/<int:subscription_id>/', views.delete_subscription, name='delete_subscription'),
    path('subscriptions/<int:subscription_id>/detail/', views.subscription_detail, name='subscription_detail'),
    
    # User Subscriptions URLs
    path('user-subscriptions/', views.user_subscriptions, name='user_subscriptions'),
    path('user-subscriptions/delete/<int:subscription_id>/', views.delete_user_subscription, name='delete_user_subscription'),
    
    # Transactions URLs
    path('transactions/', views.transactions, name='transactions'),
    
    # ML Analytics URLs
    path('ml-insights/', views.ml_insights, name='ml_insights'),
    path('ml-insights/churn-predictions/', views.churn_predictions, name='churn_predictions'),
    path('ml-insights/revenue-forecast/', views.revenue_forecast, name='revenue_forecast'),
    path('ml-insights/ltv-analysis/', views.ltv_analysis, name='ltv_analysis'),
    
    # ML API Endpoints
    path('api/predict-churn/<int:subscription_id>/', views.api_predict_churn, name='api_predict_churn'),
    path('api/revenue-forecast/', views.api_revenue_forecast, name='api_revenue_forecast'),
    path('api/ltv-prediction/<int:subscription_id>/', views.api_ltv_prediction, name='api_ltv_prediction'),
]

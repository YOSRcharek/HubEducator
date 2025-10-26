

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
]

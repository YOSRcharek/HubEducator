

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('pricing/', views.pricing, name='pricing'),
    path('web-development/', views.web_development, name='web-development'),
    path('course-details/', views.courseDetails, name='courseDetails'),
    path('user-research/', views.user_research, name='user-research'),
    path("verify-code/", views.verify_code_view, name="verify_code"),
    path('resend-code/', views.resend_code_view, name='resend_code'),

    #***********************************************************#
    #****************ResetPassword***********************#



    path('password-reset/', views.custom_password_reset, name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='ResetPassword/password_reset_done.html'), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='ResetPassword/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='ResetPassword/password_reset_complete.html'), 
         name='password_reset_complete'),
]




from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_views
from django.urls import path
from .views import google_callback
from core import views as core_views
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profil/', core_views.profil, name='profil'),
    path('pricing/', views.pricing, name='pricing'),
    path('web-development/', views.web_development, name='web-development'),
<<<<<<< HEAD
    path('certificates/', views.certificates, name='certificates'),
    path('certificates/<int:cert_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/take/<int:cert_id>/', views.take_certificate, name='take_certificate'),
    path('certificates/result/<int:attempt_id>/', views.certificate_result, name='certificate_result'),
    path('my-certificates/', views.my_certificates, name='my_certificates'),
=======
>>>>>>> main
    path('course-details/', views.courseDetails, name='courseDetails'),
    path('user-research/', views.user_research, name='user-research'),
    path("verify-code/", views.verify_code_view, name="verify_code"),
    path('resend-code/', views.resend_code_view, name='resend_code'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
<<<<<<< HEAD
    
=======
>>>>>>> main


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
<<<<<<< HEAD
=======
    
    #***********************************************************#
    #****************Payment System***********************#
    path('payment/initiate/<int:subscription_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment/webhook/', views.stripe_webhook, name='stripe_webhook'),
>>>>>>> main
]


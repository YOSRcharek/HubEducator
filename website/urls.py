

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
    path('mycourses/', views.mycourses, name='mycourses'),
    path('cours/<int:course_id>/review/', views.submit_review, name='submit_review'),
    path('review-like/<int:review_id>/', views.toggle_like_review, name='review_like'),
    path('enroll-course/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('review-delete/<int:review_id>/', views.delete_review, name='review-delete'),
    path('review-edit/<int:review_id>/', views.edit_review, name='review-edit'),
    path('pricing/', views.pricing, name='pricing'),
    path('cours/', views.courses, name='coursesUser'),
    path('course-details/<int:course_id>/', views.courseDetails, name='courseDetails'),
    path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_details, name='lesson_details'),
    path('courses/<int:course_id>/schedule/', views.schedule_course, name='schedule_course'),
    path('user-research/', views.user_research, name='user-research'),
    path("verify-code/", views.verify_code_view, name="verify_code"),
    path('resend-code/', views.resend_code_view, name='resend_code'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),


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
    
    #***********************************************************#
    #****************Payment System***********************#
    path('payment/initiate/<int:subscription_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment/webhook/', views.stripe_webhook, name='stripe_webhook'),
]


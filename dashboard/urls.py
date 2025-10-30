

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
    path('specialities/', views.SpecialityListView.as_view(), name='specialities'),
    path('specialities/add', views.SpecialityCreateView.as_view(), name='addSpecialities'),
    path('specialities/edit/<int:speciality_id>/', views.SpecialityUpdateView.as_view(), name='editSpecialities'),
    path('specialities/delete/<int:speciality_id>/', views.SpecialityDeleteView.as_view(), name='deleteSpecialities'),
    path('certificates/add/', views.create_certificate, name='certificate_add'),
    path('certificates/', views.ListCertificatView.as_view(), name='list_certificates'),
    path('certificates/edit/<int:cert_id>/', views.edit_certificate, name='editCertificate'),
    path('certificates/delete/<int:cert_id>/', views.delete_certificate, name='deleteCertificate'),
    path('certificates/preview/<int:cert_id>/', views.preview_certificate, name='previewCertificate'),
    path('certificates/results/<int:cert_id>/', views.certificate_results, name='certificate_results'),
    path('certificates/attempt/<int:attempt_id>/', views.attempt_details, name='attempt_details'),
    path('certificates/export/<int:cert_id>/', views.export_certificate_results_csv, name='export_certificate_results_excel'),
    
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
    path('transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    
    # ML Analytics URLs
    path('ml-insights/', views.ml_insights, name='ml_insights'),
    path('ml-insights/churn-predictions/', views.churn_predictions, name='churn_predictions'),
    path('ml-insights/revenue-forecast/', views.revenue_forecast, name='revenue_forecast'),
    
    # ML API Endpoints
    path('api/predict-churn/<int:subscription_id>/', views.api_predict_churn, name='api_predict_churn'),
    path('api/revenue-forecast/', views.api_revenue_forecast, name='api_revenue_forecast'),
]

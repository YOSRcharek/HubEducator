    
from django.urls import path ,include
from django.conf.urls.static import static
from django.conf import settings
from . import views
from . import ml_views
urlpatterns = [
    path('unauthorized/',views.unauthorized, name='unauthorized'),
    path('profil/',views.profil, name='profil'),
    path('my-subscription/teacher/', views.my_subscription_teacher, name='my_subscription_teacher'),
    path('my-subscription/student/', views.my_subscription_student, name='my_subscription_student'),
    path('change-subscription/teacher/', views.change_subscription_teacher, name='change_subscription_teacher'),
    path('change-subscription/student/', views.change_subscription_student, name='change_subscription_student'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('payment-history/teacher/', views.payment_history_teacher, name='payment_history_teacher'),
    path('payment-history/student/', views.payment_history_student, name='payment_history_student'),
    path('invoice/<int:transaction_id>/download/', views.download_invoice, name='download_invoice'),
    
    # ML Recommendation URLs
    path('ml/recommendation/', ml_views.recommendation_page, name='ml_recommendation'),
    path('ml/api/save-preferences/', ml_views.save_preferences, name='ml_save_preferences'),
    path('ml/api/get-recommendations/', ml_views.get_recommendations, name='ml_get_recommendations'),
    path('ml/api/record-action/', ml_views.record_user_action, name='ml_record_action'),
    path('ml/api/submit-feedback/', ml_views.submit_feedback, name='ml_submit_feedback'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
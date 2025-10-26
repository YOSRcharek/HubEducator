    
from django.urls import path ,include
from django.conf.urls.static import static
from django.conf import settings
from . import views
urlpatterns = [
    path('unauthorized/',views.unauthorized, name='unauthorized'),
    path('profil/',views.profil, name='profil'),
    path('my-subscription/teacher/', views.my_subscription_teacher, name='my_subscription_teacher'),
    path('my-subscription/student/', views.my_subscription_student, name='my_subscription_student'),
    path('payment-history/teacher/', views.payment_history_teacher, name='payment_history_teacher'),
    path('payment-history/student/', views.payment_history_student, name='payment_history_student'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
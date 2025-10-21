    
from django.urls import path ,include
from django.conf.urls.static import static
from django.conf import settings
from . import views
urlpatterns = [
    path('unauthorized/',views.unauthorized, name='unauthorized'),
    path('profil/',views.profil, name='profil'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
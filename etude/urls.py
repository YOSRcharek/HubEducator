from django.urls import path
from . import views

urlpatterns = [
    path('', views.etude_list, name='etude_list'),
    path('creer/', views.creer_groupe, name='creer_groupe'),
    path('<int:groupe_id>/rejoindre/', views.rejoindre_groupe, name='rejoindre_groupe'),
    path('<int:groupe_id>/', views.etude_detail, name='etude_detail'),
    path('<int:groupe_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:groupe_id>/rejoindre/', views.rejoindre_groupe, name='rejoindre_groupe'),


]

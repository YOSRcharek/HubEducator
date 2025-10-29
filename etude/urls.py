from django.urls import path
from . import views

urlpatterns = [
    path('', views.etude_list, name='etude_list'),
    path('creer/', views.creer_groupe, name='creer_groupe'),
    path('join/<int:group_id>/', views.join_group, name='join_group'),
    path('<int:groupe_id>/messages/', views.get_messages, name='get_messages'),
    # French alias -> use same view
    path('<int:groupe_id>/rejoindre/', views.join_group, name='rejoindre_groupe'),
    path('<int:groupe_id>/', views.etude_detail, name='etude_detail'),
]



from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profil/', views.profil, name='profil'),
    path('users/', views.users, name='users'),
    path('users/add', views.adduser, name='adduser'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edituser'),
    path('users/delete/<int:user_id>/', views.delete_user, name='deleteuser'),
]

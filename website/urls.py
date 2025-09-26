

from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('pricing/', views.pricing, name='pricing'),
    path('web-development/', views.web_development, name='web-development'),
    path('course-details/', views.courseDetails, name='courseDetails'),
    path('user-research/', views.user_research, name='user-research'),
]

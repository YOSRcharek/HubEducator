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
]

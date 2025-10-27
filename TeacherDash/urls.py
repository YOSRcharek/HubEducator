from django.urls import path
from . import views
from core import views as core_views
urlpatterns = [
    path('', views.TeacherDash, name='teacherDash'),
   path('profil/', core_views.profil, name='profil'),
    path('students/', views.students, name='students'),
    path('students/add/', views.add_student, name='add_student'),  # corrigé
    path('students/edit/<int:user_id>/', views.edit_student, name='edit_student'),  # corrigé
    path('students/delete/<int:user_id>/', views.delete_student, name='delete_student'),  # corrigé
    path('students/<int:user_id>/detail/', views.student_detail, name='student_detail'),


    path('courses/', views.courses, name='courses'),
    path('courses/add/', views.add_courses, name='add_courses'),

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
]

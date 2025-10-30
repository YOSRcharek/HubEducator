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
    path('courses/delete/<int:course_id>/', views.delete_course, name='course_delete'),
    path('courses/edit/<int:course_id>/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/detail/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/schedule/', views.schedule_course, name='schedule_course'),
    path('lessons/add/', views.add_lesson, name='add_lesson'),
    path('sublessons/add/', views.add_sublesson, name='add_sublesson'),
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),
    path('sublessons/<int:sublesson_id>/delete/', views.delete_sublesson, name='delete_sublesson'),
    path('lessons/update/', views.update_lesson, name='update_lesson'),
    path('sublessons/update/', views.update_sublesson, name='update_sublesson'),
    path('lessons/<int:lesson_id>/resources/', views.get_lesson_resources, name='get_lesson_resources'),
    path('update_visibility/<str:type>/<int:id>/', views.toggle_visibility, name='toggle_visibility'),
    path('course/<int:course_id>/assign-students/', views.assign_students_to_course, name='assign_students_to_course'),
    path('course/<int:course_id>/remove-student/', views.remove_student_from_course, name='remove_student_from_course'),
    path('review-like/<int:review_id>/', views.toggle_like_review, name='toggle_like_review'),
    path('review-delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('delete-resource/<int:resource_id>/', views.delete_resource, name='delete_resource'),

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

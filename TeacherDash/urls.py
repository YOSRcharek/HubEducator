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

# French route (existing)
    path('groupes/', views.teacher_groupes, name='teacher_groupes'),
    path('groupes/ajouter/', views.add_groupe, name='add_groupe'),

    # English alias to avoid 404 when someone visits /teacherDash/groups/
    path('groups/', views.teacher_groupes, name='teacher_groups'),
    path('groups/add/', views.add_groupe, name='add_groupe_en'),

    # edit/delete use "groups" path style in other templates — keep these as-is
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),
]

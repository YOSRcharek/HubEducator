from django.urls import path
from . import views
from core import views as core_views
from etude.models import Meeting

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

    # etude
    path('groupes/ajouter/', views.add_groupe, name='add_groupe'),

    path('groups/', views.teacher_groupes, name='teacher_groups'),

    # edit/delete groupe etude
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    # detail page for a group in the teacher dashboard
    path('groups/<int:group_id>/', views.teacher_group_detail, name='teacher_group_detail'),
    # etude resource 
    path('groups/<int:group_id>/resourceetude/add/', views.add_resource_etude, name='add_group_resourceetude'),
    # meeting
    path('groups/<int:group_id>/meetings/add/', views.add_meeting, name='add_group_meeting'),
    path('groups/<int:group_id>/meetings.json', views.meetings_json, name='group_meetings_json'),
    # meeting list for a specific group
    path('groups/<int:group_id>/meetings/', views.group_meetings, name='group_meetings'),
    # meeting details for a specific meeting
    path('groups/<int:group_id>/meetings/<int:meeting_id>/', views.meeting_detail, name='meeting_detail'),
    # meeting list for a specific group with a specific date
    path('groups/<int:group_id>/meetings/<date>/', views.group_meetings_by_date, name='group_meetings_by_date'),
    # meeting list for a specific group with a specific time
    path('groups/<int:group_id>/meetings/<time>/', views.group_meetings_by_time, name='group_meetings_by_time'),
    # meeting list for a specific group with a specific date and time
    path('groups/<int:group_id>/meetings/<date>/<time>/', views.group_meetings_by_date_time, name='group_meetings_by_date_time'),
]
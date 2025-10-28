# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Lesson, Course

@receiver(post_save, sender=Lesson)
def update_course_status_on_lesson_save(sender, instance, created, **kwargs):
    course = instance.course
    if course.lessons.exists() and course.status == 'pending':
        course.status = 'inprogress'
        course.save()

@receiver(post_delete, sender=Lesson)
def update_course_status_on_lesson_delete(sender, instance, **kwargs):
    course = instance.course
    if not course.lessons.exists() and course.status != 'pending':
        course.status = 'pending'
        course.save()

from celery import shared_task
from django.utils import timezone
from core.models import Course

@app.task
def publish_scheduled_courses():
    now = timezone.now()
    print(f"Current UTC time: {now}")
    courses = Course.objects.filter(date_publi__lte=now, published=False)
    print(f"Found courses: {courses}")
    for course in courses:
        course.published = True
        course.save()
        print(f"Published course {course.id} - {course.title}")

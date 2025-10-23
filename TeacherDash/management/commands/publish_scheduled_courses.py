from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Course

class Command(BaseCommand):
    help = "Publie automatiquement les cours planifiés"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        courses = Course.objects.filter(visible=False, publish_date__isnull=False, publish_date__lte=now)
        for course in courses:
            course.visible = True
            course.save(update_fields=['visible'])
            self.stdout.write(f"Publié: {course.title}")

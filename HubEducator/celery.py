import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HubEducator.settings')

app = Celery('HubEducator')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks dans ton app TeacherDash
app.autodiscover_tasks(['TeacherDash'])

# Pour debug
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

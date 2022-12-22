import os

from celery import Celery, shared_task

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real.settings')

app = Celery('real')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

'''
    https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
    
    celery -A proj worker -B
'''


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, send_notification.s('hello'), name='add every 10')


@shared_task
def send_notification(message):
    print(message)

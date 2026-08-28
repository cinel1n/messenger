import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'relay.settings')
app = Celery('relay', broker_connection_retry=False,
             broker_connection_retry_on_startup=True, )
app.config_from_object('django.conf:settings')

app.autodiscover_tasks()
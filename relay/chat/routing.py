from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('groups/<uuid:uuid>/', consumers.GroupConsumer.as_asgi()),
]
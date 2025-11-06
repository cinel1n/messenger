from django.urls import path
from . import views
from .views import LoginUserView, RegisterUserView

urlpatterns = [
    path('login', LoginUserView.as_view(), name='log'),
    path('register/', RegisterUserView.as_view(), name='reg'),
]

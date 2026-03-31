from django.urls import path
from . import views
from .views import LoginUserView, RegisterUserView, logout_, ProfileView

urlpatterns = [
    path('login', LoginUserView.as_view(), name='log'),
    path('register', RegisterUserView.as_view(), name='reg'),
    path('logout', logout_, name='logout'), 
    path('profile/<str:username>', ProfileView.as_view(), name="profile")

]

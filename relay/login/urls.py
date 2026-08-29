from django.urls import path
from . import views
from .views import LoginUserView, RegisterUserView, logout_, ProfileView, ProfileEditView, verify, confirm_email

urlpatterns = [
    path('login', LoginUserView.as_view(), name='log'),
    path('register', RegisterUserView.as_view(), name='reg'),
    path('logout', logout_, name='logout'), 
    path('edit', ProfileEditView.as_view(), name="edit"),
    path("verify/<uuid:uuid>", verify, name="verify"),
    path("confirm-email", confirm_email, name="confirm-email"),
    path("<str:username>", ProfileView.as_view(), name="profile"),
    
]

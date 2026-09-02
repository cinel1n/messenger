from django.urls import path
from . import views
from .views import LoginUserView, RegisterUserView, logout_, ProfileView, ProfileEditView, verify, confirm_email
from django.contrib.auth import views as auth_views
from .form import RedefinedPasswordResetForm


urlpatterns = [
    path('login', LoginUserView.as_view(), name='log'),
    path('register', RegisterUserView.as_view(), name='reg'),
    path('logout', logout_, name='logout'), 
    path('edit', ProfileEditView.as_view(), name="edit"),
    path("verify/<uuid:uuid>", verify, name="verify"),
    path("confirm-email", confirm_email, name="confirm-email"),
    path("profile/<str:username>", ProfileView.as_view(), name="profile"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
                form_class=RedefinedPasswordResetForm,
                template_name="password_reset.html",
                email_template_name="password_reset_email.html",
            ),
            name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),

    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),

    path(
        "password-change/", auth_views.PasswordChangeView.as_view(
            template_name="password_change.html"
        ), 
        name="password_change"
    ),
    path(
        "password-change/done", 
        auth_views.PasswordChangeDoneView.as_view(
            template_name="password_change_done.html"
        ), 
        name="password_change_done"
    )
    
]

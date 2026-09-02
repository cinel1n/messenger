from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth import get_user_model
from relay.celery import app
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger("django.contrib.auth")


from django.conf import settings


@app.task
def send_verification_email(id):
    User = get_user_model()
    user = get_object_or_404(User, id=id)

    verification_url = (
        settings.SITE_URL+
        reverse(
            "verify", 
            kwargs={"uuid": str(user.verification_uuid)}
        )
    )
    send_mail(
        subject='verefy your account',
        message=f'Follow this link to verify your account: {verification_url}',
        from_email=settings.EMAIL_HOST_USER,  
        recipient_list=[user.email],
        fail_silently=False, 
    )

@app.task
def send_mail_reset_password(
        subject,
        body,
        from_email,
        to_email,
        html_email=None,
        ):


    #https://docs.djangoproject.com/en/5.0/_modules/django/contrib/auth/forms/#PasswordResetForm.send_mail
    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email is not None:
        email_message.attach_alternative(html_email, "text/html")

    # try:
    email_message.send()
    # except Exception:
    #     logger.exception(
    #         "Failed to send password reset email to %s", to_email
    #     )
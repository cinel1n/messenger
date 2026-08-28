from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from relay.celery import app
from django.shortcuts import get_object_or_404


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

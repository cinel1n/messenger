from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from .form import LoginUserForm, CreateUserForm, ProfileForm
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from .tasks import *
from django.db import models
from django.views.decorators.http import require_http_methods
from .validators import compress_image
from django.utils.decorators import method_decorator
from django.contrib.auth.views import PasswordResetView
from .form import RedefinedPasswordResetForm
from django_ratelimit.decorators import ratelimit

User = get_user_model()


@method_decorator(
    ratelimit(
        key="ip", 
        rate="5/h",
        method="POST", 
        block=True
    ), 
    name="post"
)
class MyPasswordResetView(PasswordResetView):
    form_class = RedefinedPasswordResetForm


def verify(request, uuid):
    user = get_object_or_404(User, verification_uuid=uuid)
    user.is_email = True
    user.save()
    return render(request, "activate.html")


@method_decorator(
    ratelimit(key="post:username", rate="5/m",block="POST", ), 
    name="post"
)
@method_decorator(
    ratelimit(key="ip", rate="5/m",block="POST", ), 
    name="post"
)
class LoginUserView(LoginView):
    form_class = LoginUserForm
    template_name = 'login.html'

    def get_success_url(self):
        return reverse_lazy('home')


class RegisterUserView(FormView):
    form_class = CreateUserForm
    template_name = "register.html"
    success_url = reverse_lazy("log")

    def form_valid(self, form):
        avatar = form.cleaned_data["avatar"]
        if avatar:
            image = compress_image(avatar)
            form.instance.avatar = image

        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


def logout_(request):
    logout(request)
    return redirect('log')


class ProfileEditView(UpdateView):
    form_class = ProfileForm
    model = User
    template_name = "edit.html"

    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None):  # user from request
        return self.request.user

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data["email"] 
        # form.unstanse и self.request.user refer to the same object, form.initial stores the old value of the form 
        old_email = form.initial.get("email")

        if old_email != new_email: # if new email
            users_email = User.objects.filter(email__iexact=new_email, is_email=True)
            if users_email.exists(): 
                form.add_error("email", "This email is already in use.")
                return super().form_invalid(form)

            form.instance.is_email = False

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("profile", 
            kwargs={"username":self.request.user.username}
        )

class ProfileView(DetailView):
    model = User
    template_name = "profile.html"
    success_url = "/"
    
    slug_field = "username"
    slug_url_kwarg = 'username'

@require_http_methods("POST")
@ratelimit(key="user", rate="5/h", block=True)
def confirm_email(request):
    user = request.user

    users_email = User.objects.filter(email=user.email, is_email=True)  # There are no users with this verified email.

    if user.email and not user.is_email and users_email.exists():
        send_verification_email.delay(user.id)
        return HttpResponse(
        '<div id="notification" class="notification success">'
        'The message has been sent. check your email'
        '</div>'
        )
    return HttpResponse(
        '<div id="notification" class="notification error">'
        'You dont have email or you confirmed email'
        '</div>'
        )




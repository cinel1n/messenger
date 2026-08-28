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

User = get_user_model()


def verify(request, uuid):
    user = get_object_or_404(User, verification_uuid=uuid)
    user.is_email = True
    user.save()
    return render(request, "activate.html")

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
    success_url = "/"

    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self, queryset=None): 
        return self.request.user
        

class ProfileView(DetailView):
    model = User
    template_name = "profile.html"
    success_url = "/"
    
    slug_field = "username"
    slug_url_kwarg = 'username'

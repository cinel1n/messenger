from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from .form import LoginUserForm, CreateUserForm



class LoginUserView(LoginView):
    form_class = LoginUserForm
    template_name = 'login.html'


class RegisterUserView(FormView):
    form_class = CreateUserForm
    template_name = "register.html"
    success_url = reverse_lazy("log")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


# class LoginView(FormView):
#     form_class = UserCreationForm
#     template_name = "login.html"
#
#
#     def get_form_class(self):
#         form_type = self.request.POST.get("form_type")
#         if form_type == 'register':
#             return UserCreationForm
#         return LoginUserForm
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         form_type = self.request.POST.get("form_type")
#         if form_type == 'register':
#             context[]
#
#     def form_valid(self, form):
#         form_type = self.request.POST.get("form_type")
#
#         if form_type == "register" :
#             email = form.cleaned_data['email']
#             if not email:
#                 form.add_error('email', "The email field is empty")
#                 return self.form_invalid(form)
#
#             user = form.save()
#             login(self.request, user)
#             return self.form_valid(form)
#
#         if form_type == "login":
#             username = form.cleaned_data.get("username")
#             password = form.cleaned_data.get("password")
#             user = authenticate(self.request, username=username, password=password)
#
#             if user:
#                 login(self.request, user)
#                 return self.form_valid(form)
#
#             form.add_error('username', "Invalid username or invalid password")
#
#         return super().form_invalid(form)


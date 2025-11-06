from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id':"loginName"}), label="Username", max_length=15)
    password = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'id':"loginPassword"}), label="Password", max_length=50)


class CreateUserForm(UserCreationForm):
    username = forms.CharField(label="Username", max_length=50, widget=forms.TextInput(attrs={"class":"form-control", 'id':"loginName"}))
    first_name = forms.CharField(label="First Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control", 'id':"RegisterName"}))
    last_name = forms.CharField(label="Last Name", max_length=50, widget=forms.TextInput(attrs={"class":"form-control", 'id':"RegisterLastName"}))
    email = forms.EmailField(label="Email", max_length=50, widget=forms.TextInput(attrs={"class":"form-control", 'id':"RegisterEmail"}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': "registerPassword",
        }))
    password2 = forms.CharField(label="Repeat password" ,widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': "registerRepeatPassword",
        }))

    data_entry = forms.BooleanField(required=True, label=' I have read and agree to the terms', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'data_entry')
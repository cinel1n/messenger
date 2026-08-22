from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import User

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return User

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            username=username, 
            password=password, 
            **extra_fields, 
        )


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True, default="")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQIORED_FIELDS = []

    def __str__(self):
        return f"{self.username} {self.first_name} {self.last_name}"
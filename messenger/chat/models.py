from datetime import datetime

from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4

from django.urls import reverse

User = get_user_model()

class Group(models.Model):
    class GroupType(models.TextChoices):
        PRIVATE = 'private'
        PUBLIC = 'public'

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=30, blank=True)
    members = models.ManyToManyField(User, through='GroupMemberModel')
    type = models.CharField(max_length=10, choices=GroupType.choices, default=GroupType.PRIVATE)


    def get_absolute_url(self):
        return reverse("group", args=[str(self.uuid)])

    def add_user_to_group(self, user: User):
        self.members.add(user)
        self.event_set.create(type="Join", user=user)
        self.save()

    def remove_user_from_group(self, user: User):
        self.members.remove(user)
        self.event_set.create(type="Left", user=user)
        self.save()

    def last_message(self):
        return self.message_set.order_by("-timestamp").first()

    def get_name(self, user):
        if self.type == self.GroupType.PUBLIC:
            return self.name
            
        member = [i for i in self.members.all() if i != user][0]
        return member
        


class GroupMemberModel(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("group", "user")

class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author}: {self.content}"



class Event(models.Model):
    CHOICES = [
        ("Join", "join"),
        ("Left", "left")
        ]
    type = models.CharField(choices=CHOICES, max_length=10)
    description= models.CharField(help_text="A description of the event that occurred",\
    max_length=50, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group ,on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.description = f"{self.user} {self.type} the {self.group.name} group"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.description}"
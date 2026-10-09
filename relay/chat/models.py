from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4
from login.validators import validate_avatar_size
from django.urls import reverse
from relay.settings import DEFAULT_AVATAR
from django.templatetags.static import static
from django.db import transaction


User = get_user_model()

class Group(models.Model):
    class GroupType(models.TextChoices):
        PRIVATE = 'private'
        PUBLIC = 'public'

    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=30, blank=True)
    members = models.ManyToManyField(User, through='GroupMemberModel')
    avatar = models.ImageField(upload_to="avatars/", blank=True, default="", 
        validators=[validate_avatar_size])
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=GroupType.choices, default=GroupType.PRIVATE)


    def get_absolute_url(self):
        return reverse("group", args=[str(self.uuid)])

    @transaction.atomic
    def add_user_to_group(self, user: User):
        self.members.add(user)
        self.event_set.create(type="Join", user=user)
        

    def last_message(self):
        return getattr(self, "last_message_content", None)
    
    def get_name(self, user=None):
        if self.type == self.GroupType.PUBLIC:
            return self.name

        if user:
            companion = next(
                (
                    member
                    for member in self.members.all()
                    if member.id != user.id
                ),
                None,
            )

            return companion

        return None

    def get_avatar(self, user=None):
        if self.type == self.GroupType.PUBLIC:
            if self.avatar:
                return self.avatar.url
            return static(DEFAULT_AVATAR)

        if user:
            companion = next(
                (
                    member
                    for member in self.members.all()
                    if member.id != user.id
                ),
                None,
            )

            return companion.get_avatar_url()

        return static(DEFAULT_AVATAR)


class GroupMemberModel(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_creator = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"], 
                name="unique_group_member"
            )
        ]

    @transaction.atomic
    def remove_user_from_group(self):
        self.group.event_set.create(type="Left", user=self.user)
        self.delete()


class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=4096)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.author}: {self.content}"
    
    def type_content(self):
        return "message"

    # B-tree index
    class Meta:
        indexes = [
            models.Index(fields=["group", "-timestamp"], name="msg_group_ts_idx"),
        ]


class Event(models.Model):
    CHOICES = [
        ("Join", "join"),
        ("Left", "left")
        ]
    type = models.CharField(choices=CHOICES, max_length=10)
    description= models.CharField(help_text="A description of the event that occurred",\
    max_length=150, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group ,on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.description = f"{self.user} {self.type} the {self.group.name} group"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.description}"

    def type_content(self):
        return "event"

    class Meta:
        indexes = [
            models.Index(fields=["group", "-timestamp"], name="event_group_ts_idx"),
        ]
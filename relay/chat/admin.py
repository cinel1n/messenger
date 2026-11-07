from django.contrib import admin
from .models import *


class MessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', "timestamp"]


class GroupMemberInline(admin.TabularInline):
    model = GroupMemberModel
    extra = 0


class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', "uuid"]
    inlines = [GroupMemberInline]


class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'is_admin']


class AttachmentsAdmin(admin.ModelAdmin):
    list_display = ['original_name']

admin.site.register(Message, MessageAdmin)
admin.site.register(Event)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMemberModel, GroupMemberAdmin)
admin.site.register(AttachmentsModel, AttachmentsAdmin)
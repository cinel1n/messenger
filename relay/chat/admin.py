from django.contrib import admin
from .models import *

class MessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'content']

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']

class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'is_admin']


admin.site.register(Message, MessageAdmin)
admin.site.register(Event)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMemberModel, GroupMemberAdmin)

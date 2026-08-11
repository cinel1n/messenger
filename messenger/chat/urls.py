
from django.urls import path, include
from .views import *
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path("groups/<uuid:uuid>/", HomeView.as_view(), name="group"),
    path("search", accounts_search_view, name="search"),
    path("user/<str:username>", start_chat_view, name="user"),
    path("create-group", CreateGroupView.as_view(), name='create_group'),
    path("delete-chat/<str:uuid>", DeleteChatView.as_view(), name='delete-chat'),
    path("group-info/<str:uuid>", GroupInfoView.as_view(), name="group-info"),
    path("group-member/delete/<int:id>", delete_group_member, name="delete-group-member")

]
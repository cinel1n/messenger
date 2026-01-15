
from django.urls import path, include
from .views import HomeView, start_chat_view, AccountsSearchView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path("groups/<uuid:uuid>/", HomeView.as_view(), name="group"),
    path("search", AccountsSearchView.as_view(), name="search"),
    path("user/<str:username>", start_chat_view, name="user"),
]
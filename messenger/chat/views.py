from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, TemplateView
from .models import Group

class HomeView(TemplateView):
    model = Group
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user

        if self.request.user.is_authenticated:
            context['groups'] = self.model.objects.filter(members=self.request.user)
        else:
            context['groups'] = self.model.objects.none()
        return context


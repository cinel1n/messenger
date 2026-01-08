from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from .models import Group
from django.contrib.auth.decorators import login_required

class HomeView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "home.html"
    login_url = reverse_lazy('log')

    def get_queryset(self):
        return Group.objects.filter(members=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            group_uuid = self.kwargs['uuid']
        except:
            group_uuid = None

        if group_uuid:
            group = get_object_or_404(Group, uuid=group_uuid)
            messages = group.message_set.all()
            events = group.event_set.all()
            message_and_event_list = [*messages, *events]
            sorted_message_event_list = sorted(message_and_event_list, key=lambda x: x.timestamp)
            group_member = [i for i in group.members.all() if i != self.request.user][0]

            context['group'] = group
            context['messages'] = sorted_message_event_list
            context['group_member'] = group_member
            context['last_message'] = sorted_message_event_list[-1] if len(sorted_message_event_list)>0 else ""

        context["user"] = self.request.user
        context['groups'] = self.model.objects.filter(members=self.request.user)

        return context



from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, FormView
from .models import Group, User, GroupMemberModel
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .form import GroupForm
from django.db.models import Count

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
            members = group.members.all()

            if group.type == group.GroupType.PUBLIC:
                group_member = f"{len(members)} участников"
            else:
                group_member = [i for i in members if i != self.request.user][0]

            context['group'] = group
            context['messages'] = sorted_message_event_list
            context['group_member'] = group.get_name(self.request.user)

        context["user"] = self.request.user
        group_list = []

        for group in self.model.objects.filter(members=self.request.user):
            if group.type == group.GroupType.PUBLIC:
                group_list.append([group.name, group])
            else:
                group_name = [i for i in group.members.all() if i != self.request.user][0].username
                group_list.append([group_name, group])

        context['groups'] = group_list

        return context



class AccountsSearchView(LoginRequiredMixin, ListView):
    model = User
    template_name = "accounts.html"

    def get_queryset(self):
        users = User.objects.filter(username__istartswith = self.request.GET.get("search_user"))
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.request.GET.get("search_user")
        context['search_username'] = username
        return context


def start_chat_view(request, username):
    user = User.objects.get(username=username)
    group = Group.objects.filter(members=user).filter(members=request.user).filter(type=Group.GroupType.PRIVATE).first()

    if user == request.user:
        return redirect("home")

    if not group:
        group = Group.objects.create()
        group.members.add(request.user, user)
    
    url = reverse('group', args=[group.uuid])

    return redirect(url)


class CreateGroupView(FormView):
    model = Group
    form_class = GroupForm
    template_name = "create_group.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        group = form.save(commit=False)
        group.type = group.GroupType.PUBLIC
        group.save()

        GroupMemberModel.objects.create(
            group=group, 
            user=self.request.user, 
            is_admin=True
        )
        for user in form.cleaned_data["members"]:
            if user != self.request.user:
                GroupMemberModel.objects.create(
                    group=group, 
                    user=user, 
                )

        return super().form_valid(form)

    # передает юзера в форму
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  
        return kwargs



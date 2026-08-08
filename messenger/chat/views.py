from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, FormView, DeleteView, DetailView
from .models import Group, User, GroupMemberModel, Event
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .form import GroupForm
from django.contrib import messages
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
            # members = group.members.all()

            context['group'] = group
            context['messages_event'] = sorted_message_event_list
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


class GroupInfoView(DetailView):
    model = Group
    template_name = "group-info.html"

    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    

# class AccountsSearchView(LoginRequiredMixin, ListView):
#     model = User
#     template_name = "accounts.html"

#     def get_queryset(self):
#         users = User.objects.filter(username=self.request.GET.get("search_user"))
#         return users

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         username = self.request.GET.get("search_user")
#         context['search_username'] = username
#         return context

def accounts_search_view(request):
    username = request.GET.get('search_user')
    result = User.objects.filter(username=username)

    if result.count() == 1:
        return redirect("profile", username=username)

    messages.error(request,"user not found")
    return redirect(request.META.get("HTTP_REFERER", "home"))


class DeleteChatView(DeleteView):
    model = Group
    success_url = "/"
    template_name = "delete-chat.html"

    slug_field = "uuid"
    slug_url_kwarg = "uuid"


def start_chat_view(request, username):
    user = get_object_or_404(User, username=username)
    group = Group.objects.filter(members=user).filter(members=request.user).filter(type=Group.GroupType.PRIVATE).first()

    if user == request.user:
        return redirect("home")

    if not group:
        group = Group.objects.create()
        group.add_user_to_group(user)
        group.add_user_to_group(request.user)
    
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
            user=self.request.user,  # добавляется в модель GroupModel
            is_admin=True
        )
        for user in form.cleaned_data["members"]:
            GroupMemberModel.objects.create(
                group=group, 
                user=user, 
            )
            Event.objects.create(type="Join", user=user, group=group)
        return super().form_valid(form)

    # передает юзера в форму
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  
        return kwargs


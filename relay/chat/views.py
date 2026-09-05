from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, FormView, DeleteView, DetailView, UpdateView
from .models import Group, User, GroupMemberModel, Event
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .form import GroupForm
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Count
from rest_framework import viewsets
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer
from login.validators import compress_image


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
            member_group = get_object_or_404(GroupMemberModel, group=group, user=self.request.user)

            context["is_delete"] = False
            if group.type == group.GroupType.PRIVATE or member_group.is_creator:
                context["is_delete"] = True

            context['group'] = group
            context['messages_event'] = sorted_message_event_list
            context['group_member'] = group.get_name(self.request.user)

        group_list = []

        for group in self.object_list:
            if group.type == group.GroupType.PUBLIC:
                data = {
                    "name": group.name, 
                    "group": group, 
                    "avatar":group.avatar, 
                }

            else:
                member = group.get_name(self.request.user)
                data = {
                    "name": member.first_name, 
                    "group": group, 
                    "avatar":member.avatar, 
                }
            group_list.append(data)

        context['groups'] = group_list

        return context


class GroupInfoView(DetailView):
    model = Group
    template_name = "group-info.html"

    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        current_groupmember = get_object_or_404(GroupMemberModel, user=self.request.user, group=group)
        
        context['current_groupmember'] = current_groupmember
        context['members_info'] = GroupMemberModel.objects.filter(group=group)
        return context
    

class GroupEditView(UpdateView):
    model = Group
    success_url = "/"
    template_name = "group-edit.html"
    form_class = GroupForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        current_groupmember = get_object_or_404(GroupMemberModel, user=self.request.user, group=group)
        
        context['current_groupmember'] = current_groupmember
        context['members_info'] = GroupMemberModel.objects.filter(group=group)
        return context
    
    def dispatch(self, request, *args, **kwargs): 
        # rights check
        group = self.get_object()
        member = get_object_or_404(
            GroupMemberModel, 
            group=group, 
            user=request.user
        )
        if not (member.is_admin or member.is_creator):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user  
        group = self.get_object()
        groups = user.group_set.all()

        users = User.objects.filter(group__in=groups).exclude(id=user.id).exclude(
            groupmembermodel__group=group
        ).distinct()
        kwargs['members_queryset'] = users
        kwargs['edit'] = True
        return kwargs
    
    def form_valid(self, form):
        group = self.get_object()

        group.name = form.cleaned_data["name"]
        group.avatar = form.cleaned_data["avatar"]
        group.save()
        for member in form.cleaned_data["members"]:
            GroupMemberModel.objects.create(group=group, user=member)
            Event.objects.create(type="Join", user=member, group=group)

        return HttpResponseRedirect(self.get_success_url())


def accounts_search_view(request):
    username = request.GET.get('search_user')
    result = User.objects.filter(username=username)

    if result.count() == 1:
        return redirect("profile", username=username)

    messages.error(request,"user not found")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@require_http_methods(['DELETE'])
def delete_group_member(request, id):
    user = request.user  # who deletes
    member = get_object_or_404(GroupMemberModel, id=id) # the one who is being removed
    group = member.group

    user_gm = get_object_or_404(GroupMemberModel, user=user, group=group) # who deletes
    
    if user_gm.is_creator or (user_gm.is_admin and not member.is_admin):
        member.delete() 
        Event.objects.create(type="Left", user=member.user, group=group)
        return HttpResponse("")
    
    return HttpResponse("You cannot delete this user", status=403)
    

@require_http_methods(["POST"])
def admin_group_member(request, id):
    user = request.user
    member = get_object_or_404(GroupMemberModel, id=id) 
    group = member.group

    user_gm = get_object_or_404(GroupMemberModel, user=user, group=group) 

    if user_gm.is_creator:
        member.is_admin = True if not member.is_admin else False
        member.save()
        return HttpResponse("")

    elif user_gm.is_admin and not member.is_admin:
        member.is_admin = True
        member.save()
        return HttpResponse("")
        
    return HttpResponse("You don't have righs")


class DeleteChatView(DeleteView):
    model = Group
    success_url = "/"
    template_name = "delete-chat.html"

    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        group = self.get_object()
        group_member = get_object_or_404(GroupMemberModel, user=user, group=group)

        if group_member.is_creator or group.type == group.GroupType.PRIVATE:
            return super().dispatch(request, *args, **kwargs)

        return HttpResponseForbidden()


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
        group = form.save(commit=False) # creates a model object but does not save it
        group.type = group.GroupType.PUBLIC

        if group.avatar:
            avatar = compress_image(group.avatar)
            group.avatar = avatar
            
        group.save()

        GroupMemberModel.objects.create(
            group=group, 
            user=self.request.user,  # добавляется в модель GroupModel
            is_admin=True, 
            is_creator=True
        )
        for user in form.cleaned_data["members"]:
            GroupMemberModel.objects.create(
                group=group, 
                user=user, 
            )
            Event.objects.create(type="Join", user=user, group=group)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user  
        groups = user.group_set.all()

        kwargs["members_queryset"] = (
            User.objects
            .filter(group__in=groups)
            .exclude(id=user.id)
            .distinct()
        )

        return kwargs


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMemberModel.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
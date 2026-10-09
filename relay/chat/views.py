from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, FormView, DeleteView, DetailView, UpdateView
from .models import Group, User, GroupMemberModel, Event, Message
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .form import GroupForm
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Count
from rest_framework import viewsets
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import permissions
from .serializers import UserSerializer, GroupSerializer
from login.validators import compress_image
from relay.settings import LIMIT_MESSAGE
from django.db.models import OuterRef, Subquery
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from django.db.models import Q
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce


class HomeView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "home.html"
    login_url = reverse_lazy('log')

    def get_queryset(self):

        last_message = Message.objects.filter(
            group=OuterRef("pk") # pk группы, которую обрабатывает запрос 
        ).order_by("-timestamp", "-id")
        
        groups = Group.objects.filter(
            members=self.request.user
        ).annotate( # добавляет новое поле к каждому элементу в QuerySet
            last_message_time=Subquery( # позволяет вставить полноценный SQL-подзапрос внутрь этого аннотирования
                last_message.values("timestamp")[:1]
            ),
            last_message_content=Subquery(
                last_message.values("content")[:1]
            ),
            last_activity=Coalesce("last_message_time", "timestamp"),
        ).order_by(
            "last_activity"
        ).prefetch_related(
            "members"
        )

        return groups[::-1]


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        group_list = []

        for group in self.object_list:
            data = {
                "name": group.get_name(self.request.user), 
                "group": group, 
                "avatar":group.get_avatar(self.request.user), 
            }
    
            group_list.append(data)

        context['groups'] = group_list

        return context

# генерация сообщений группы, количество которых ограничено 
def chat_data(request, uuid):
    group = get_object_or_404(Group, uuid=uuid, members=request.user)

    # дата самаго старшего сообщения
    before = request.GET.get("before")
    before_data = None 


    messages = Message.objects.filter(
        group=group
    ).select_related(
        "author"
    )

    events = Event.objects.filter(
        group=group
    )

    max_message = LIMIT_MESSAGE
    
    if before:
        try:
            before_dt = parse_datetime(before)
        except ValueError:
            return HttpResponse("Date is incorect", 400)

        # все сообщения и события, что старше before
        messages = messages.filter(
            timestamp__lt=before_dt
        )
        events = events.filter(
            timestamp__lt=before_dt
        )

    # сортировка по дате и id 
    messages = messages.order_by("-timestamp", "-id")[:max_message]
    events = events.order_by("-timestamp", "-id")[:max_message]
    
    message_and_event_list = [*messages, *events]
    # элементы расположены от старшего к младшему, вычесление индекса, с которого можно брать элементы
    len_item = len(message_and_event_list) 
    with_item = len_item-max_message if len_item > max_message else 0

    items = sorted(message_and_event_list, key=lambda x: (x.timestamp, x.id))[with_item:]
    return items


@login_required
def old_message(request, uuid):
    items = chat_data(request=request, uuid=uuid)
    return JsonResponse({
        "messages": [
            {
                "id": item.id,
                "type": item.type_content(),
                "timestamp": item.timestamp.isoformat(),

                "content": (
                    item.content
                    if item.type_content() == "message"
                    else item.description
                ),

                "author": (
                    item.author.username
                    if item.type_content() == "message"
                    else None
                ),
                "avatar": item.author.get_avatar_url() if item.type_content() == "message" else None, 
            }
            for item in items[::-1]
        ], 
        "next_cursor": (
            items[0].timestamp.isoformat()
            if items
            else None
        ),   
    }
    )


class ChatView(HomeView):
    model = Group
    template_name = "home.html"
    login_url = reverse_lazy('log')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_uuid = self.kwargs['uuid']
        group = get_object_or_404(Group, uuid=group_uuid, members=self.request.user)

        items_chat = chat_data(self.request, group_uuid)
        
        if items_chat:
            context["next_cursor"] = items_chat[0].timestamp.isoformat()
        else:
            context["next_cursor"] = None

        
        member_group = get_object_or_404(GroupMemberModel, group=group, user=self.request.user)

        # удаление чата 
        context["is_delete"] = False
        if group.type == group.GroupType.PRIVATE or member_group.is_creator:
            context["is_delete"] = True
        
        context['group'] = group
        context['messages_event'] = items_chat
        context['group_member'] = group.get_name(self.request.user)

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
    
    @transaction.atomic # атомарная запись в бд
    def form_valid(self, form):
        group = self.get_object()

        group.name = form.cleaned_data["name"]
        new_ava = form.cleaned_data['avatar']
        
        if new_ava:
            group.avatar = compress_image(new_ava)

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
    return redirect(request.META.get("HTTP_REFERER", "home")) # redirect на ранее посещенную страницу, инача на главную


@require_http_methods("DELETE")
def delete_message_view(request, pk):
    message = get_object_or_404(Message, id=pk)
    if message.author != request.user:
        return HttpResponse("You cannot delete this message", 403)
    
    message.delete()
    return HttpResponse("Message was deleted")

@require_http_methods(['DELETE'])
def delete_group_member(request, id):
    user = request.user  # who deletes
    member = get_object_or_404(GroupMemberModel, id=id) # the one who is being removed
    group = member.group
    
    user_gm = get_object_or_404(GroupMemberModel, user=user, group=group) # who deletes
    
    if (user_gm.is_creator and not member.is_creator) or \
        (user_gm.is_admin and not member.is_admin and \
            not member.is_creator):

        member.remove_user_from_group() 

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}", 
            {
                "type":"force_disconnect", 
                "group_uuid":str(group.uuid),
                "message": "you've been deleted from the group "
            }
        )
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, FormView, DeleteView, DetailView, UpdateView
from .models import Group, User, GroupMemberModel, Event, Message, AttachmentsModel
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .form import GroupForm
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Count
from rest_framework import viewsets
from django.http import FileResponse
from channels.layers import get_channel_layer
from django.core.exceptions import BadRequest
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
import os
from PIL import Image
from relay.settings import BASE_DIR
from django.views.decorators.http import require_POST



class HomeView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "home.html"
    login_url = reverse_lazy('log')

    def get_queryset(self):

        last_message = Message.objects.filter(
            group=OuterRef("pk") # pk группы, которую обрабатывает запрос 
        ).order_by("-timestamp", "-id")
        
        group_member_model = GroupMemberModel.objects.filter(
            user=self.request.user, 
            group=OuterRef("pk")
            )[:1]

        unread = (
            Message.objects
            .filter(group=OuterRef("pk"), id__gt=OuterRef("last_read_message_id"))
            .exclude(author=self.request.user)
            .order_by()
            .values("group")
            .annotate(c=Count("pk"))
            .values("c")
        )

        groups = Group.objects.filter(
            members=self.request.user
        ).annotate( # добавляет новое поле к каждому элементу в QuerySet
            last_message_time=Subquery( # позволяет вставить полноценный SQL-подзапрос внутрь этого аннотирования
                last_message.values("timestamp")[:1]
            ),
            last_message_content=Subquery(
                last_message.values("content")[:1]
            ),
            # права и данные юзера в этой группе 
            last_read_message_id=Subquery(
                group_member_model.values("last_read_message_id")
            ),
            unread_count=Coalesce(Subquery(unread), 0),
            last_activity=Coalesce("last_message_time", "timestamp"),
            
        ).order_by(
            "-last_activity"
        ).prefetch_related(
            "members"
        )
        
        return groups


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        group_list = []
        
        for group in self.object_list:
            
            data = {
                "name": group.get_name(self.request.user), 
                "group": group, 
                "avatar":group.get_avatar(self.request.user), 
                "no_read_message": group.unread_count if group.unread_count != 0 else ""
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

    attachments = AttachmentsModel.objects.filter(
        message=OuterRef("pk")
    )

    messages = Message.objects.filter(
        group=group
    ).prefetch_related(
        "attachmentsmodel_set"
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
            before_dt = None

        if before_dt is None:
            raise BadRequest("Invalid 'before'")

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
    data = []
    for item in items[::-1]:
        if item.type_content() == "message":
            data.append(
                {
                    "id": item.id,
                    "type": item.type_content(),
                    "timestamp": item.timestamp.isoformat(),
                    "content": item.content,
                    "author": item.author.username,
                    "avatar": item.author.get_avatar_url(), 
                    "attachments" :
                        [   
                            {
                                "id": att.id,
                                "url": att.file.url, 
                                "name": att.original_name,
                                "kind": att.kind
                            }
                            for att in item.attachmentsmodel_set.all()
                        ] 
                }
            ), 
        elif item.type_content() == "event":
            data.append(
                {
                    "id": item.id,
                    "type": item.type_content(),
                    "timestamp": item.timestamp.isoformat(),
                    "content": item.description,    
                }
            ), 
        else:
            return HttpResponse({"error":"unknown data type"},  400)

    return JsonResponse({
        "messages": data, 
        "next_cursor": (
            items[0].timestamp.isoformat()
            if items
            else None
        ),   
    })


class ChatView(HomeView):
    model = Group
    template_name = "home.html"
    login_url = reverse_lazy('log')

    def get_context_data(self, **kwargs):
        
        group_uuid = self.kwargs['uuid']
        group = get_object_or_404(Group, uuid=group_uuid, members=self.request.user)

        items_chat = chat_data(self.request, group_uuid)

        member_group = get_object_or_404(GroupMemberModel, group=group, user=self.request.user)

        ids_message = [i.id for i in items_chat if i.type_content() == "message"]
        if ids_message:
            id_max = max(ids_message)
            member_group.last_read_message_id = id_max
            member_group.save()

        context = super().get_context_data(**kwargs)
        if items_chat:
            context["next_cursor"] = items_chat[0].timestamp.isoformat()
        else:
            context["next_cursor"] = None

        context["is_delete"] = group.type == group.GroupType.PRIVATE or member_group.is_creator
        
        context['group'] = group
        context['messages_event'] = items_chat
        context['group_name'] = group.get_name(self.request.user)

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


    channel_layer = get_channel_layer()
    
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


@login_required
@transaction.atomic
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


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
OOXML = "application/vnd.openxmlformats-officedocument."

OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"          # контейнер старых .doc/.xls/.ppt
FILE_TYPES = {                    
    ".pdf":  ("application/pdf", (0, (b"%PDF-",))),
    ".txt":  ("text/plain", None),
    ".docx": (OOXML + "wordprocessingml.document", (0, (b"PK\x03\x04",))),
    ".xlsx": (OOXML + "spreadsheetml.sheet", (0, (b"PK\x03\x04",))),
    ".pptx": (OOXML + "presentationml.presentation", (0, (b"PK\x03\x04",))),
    ".zip":  ("application/zip", (0, (b"PK\x03\x04",))),
    ".doc":  ("application/msword", (0, (OLE2,))),
    ".xls":  ("application/vnd.ms-excel", (0, (OLE2,))),
    ".ppt":  ("application/vnd.ms-powerpoint", (0, (OLE2,))),
    ".rtf":  ("application/rtf", (0, (b"{\\rtf",))),
    ".rar":  ("application/vnd.rar", (0, (b"Rar!\x1a\x07",))),
    ".7z":   ("application/x-7z-compressed", (0, (b"7z\xbc\xaf\x27\x1c",))),
    ".mp3":  ("audio/mpeg", (0, (b"ID3", b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2"))),
    ".ogg":  ("audio/ogg", (0, (b"OggS",))),
    ".mp4":  ("video/mp4", (4, (b"ftyp",))),
    ".m4a":  ("audio/mp4", (4, (b"ftyp",))),
    ".mov":  ("video/quicktime", (4, (b"ftyp", b"moov", b"wide", b"mdat"))),
}


def validate_file(file):
    from relay.settings import MAX_IMAGE_BYTES, MAX_FILE_BYTES

    name, ext = [os.path.splitext(file.name)[i] for i in range(2)]
    ext = ext.lower()
    if ext in IMAGE_EXTS:
        if file.size > MAX_IMAGE_BYTES:
            raise ValidationError(f"file is too large (max {MAX_IMAGE_BYTES/(1024**2)} mb)")
        
        try: # используем Pillow 
            with Image.open(file) as img:
                img.verify()
                if "." + img.format.lower() not in IMAGE_EXTS: # открывает файл и проверяет содержимое на разрешение 
                    raise ValidationError("Unsupported image format", code="unsupported")

        except Exception:
            raise ValidationError("The file is corrupted or is not an image")

        finally:
            file.seek(0) # восстанавливается указатель файла

        return True

    elif ext in FILE_TYPES:
        if file.size > MAX_FILE_BYTES:
            raise ValidationError(f"file is too large (max {MAX_FILE_BYTES/(1024**2)} mb)")

        content_type, offset_magic = FILE_TYPES[ext]
        head = file.read(1024) 
        file.seek(0)
        if offset_magic:
            offset, magic_bytes = offset_magic

            if not head.startswith(magic_bytes, offset): # есть ли магические байти и совпадают ли они с должными магическими байтами  
                raise ValidationError("File content does not match its extension")

        elif ext == ".txt" and b"\x00" in head:
            raise ValidationError("File content does not match its extension")

        return True
    else:
        raise ValidationError("invalid file extension")


@require_POST
def file_upload(request, uuid):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    group = get_object_or_404(Group, uuid=uuid, members=request.user)
    file = request.FILES.get("file")

    if file is None:
        return JsonResponse({"error": "file is None"}, status=400)
    
    name, ext = [os.path.splitext(file.name)[i] for i in range(2)]
    ext = ext.lower()

    try:
        vf = validate_file(file)
    except ValidationError as error:
        return JsonResponse({"error": error.message}, status=error.code)

    org_name = file.name.strip()[:240]
    with transaction.atomic():
        attachment = AttachmentsModel.objects.create(
            file=file, 
            original_name=org_name, 
            kind=AttachmentsModel.Kind.IMAGE if ext in IMAGE_EXTS else AttachmentsModel.Kind.FILE,
            size=file.size,
            group=group, 
            author=request.user
        )
        
    return JsonResponse({
        "pk_attachment" : attachment.id
    })


def attachments_download(request, pk):
    att = get_object_or_404(AttachmentsModel, pk=pk, group__members=request.user)
    file = att.file.open("rb")
    
    return FileResponse(file, as_attachment=True, filename=att.original_name)

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
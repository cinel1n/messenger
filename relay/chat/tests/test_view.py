from django.test import TestCase
from chat.models import Group, GroupMemberModel, Message, Event
import uuid
from chat.form import GroupForm
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatHomeTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="testusername002", first_name="user2",  password="testuserpassword001")
        self.user = User.objects.create_user(username='testusername001', first_name="user1", password="testuserpassword001")

        self.url = reverse("home")

        self.client.login(username='testusername001', password="testuserpassword001")
        
        self.group = Group.objects.create()
        self.group.members.add(self.user, self.user1)
        
        Message.objects.create(author=self.user, content="hello!", group=self.group)

    def test_context_home(self):
        self.response = self.client.get(self.url)
        groups = self.response.context.get("groups")
        
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "home.html")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].get("group"), self.group)
        self.assertEqual(groups[0].get("name"), self.user1.first_name)
        self.assertEqual(self.response.context.get("user"), self.user)

    def test_none_context_logout(self):
        self.client.logout()
        self.response = self.client.get(self.url)
        self.assertEqual(self.response.status_code, 302)

    def test_uuid_context_group(self):
        self.url_uuid = reverse("group", args=[self.group.uuid, ])
        self.response_uuid = self.client.get(self.url_uuid)

        self.assertEqual(self.response_uuid.status_code, 200)
        group = self.response_uuid.context.get("group")
        messages = self.response_uuid.context.get("messages_event")
        group_member = self.response_uuid.context.get("group_member")
        mess_content = messages[0].content 
        self.assertEqual(group_member, self.user1)
        self.assertEqual(self.group, group)
        self.assertEqual(mess_content, "hello!")
    
    def test_name_group(self):
        name_group = "cool girls"

        group = Group.objects.create(type=Group.GroupType.PUBLIC, name=name_group)
        group.members.add(self.user, self.user1)
        response = self.client.get(self.url)
        
        groups = response.context.get("groups")
        data_content = {
            "name":name_group, 
            "group": group, 
            "avatar":group.avatar
        }
        self.assertIn(data_content, groups)


class AccountsSearchTest(TestCase):
    def setUp(self):
        self.url = reverse("search")
        self.user1 = User.objects.create_user(username="testusername002", password="testuserpassword001")
        self.user = User.objects.create_user(username='testusername001', password="testuserpassword001")

        self.client.login(username='testusername001', password="testuserpassword001")

    def test_redirect_on_profile(self):
        self.response = self.client.get(self.url, {"search_user":self.user1.username})
        self.profile_url = reverse("profile", kwargs={"username":self.user1.username})
        self.assertEqual(self.response.status_code, 302) # redirect
        self.assertRedirects(self.response, 
            self.profile_url
        )
    
    def test_redirect_on_home_not_user(self):
        self.response = self.client.get(self.url, {"search_user": "none_user"})
        # redirect на главную страницу, т.к пользователя с таким username не существует
        self.assertEqual(self.response.status_code, 302)
        self.assertRedirects(self.response, 
            reverse("home") 
        )

    # def test_context_full_username(self):
    #     self.response = self.client.get(self.url, {"search_user":self.user1.username})

    #     result = self.response.context.get("object_list")
    #     search_username = self.response.context.get("search_username")

    #     self.assertEqual(self.response.status_code, 200)
    #     self.assertEqual(result.count(), 1)
    #     self.assertEqual(result[0], self.user1)
    #     self.assertEqual(search_username, self.user1.username)
    #     self.assertTemplateUsed(self.response,"accounts.html")

    
    # def test_context_part_username(self):
    #     self.response = self.client.get(self.url, {"search_user":self.user1.username[:1]})

    #     result = self.response.context.get("object_list")
    #     search_username = self.response.context.get("search_username")

    #     self.assertEqual(self.response.status_code, 200)
    #     self.assertEqual(result.count(), 0)
    #     self.assertEqual(search_username, self.user1.username[:1])

    
    # def test_context_logout(self):
    #     self.client.logout()
    #     self.response = self.client.get(self.url)

    #     self.assertEqual(self.response.status_code, 302)

    # def test_context_none_searchuser(self):
    #     self.response = self.client.get(self.url)

    #     result = self.response.context.get("object_list")
    #     search_username = self.response.context.get("search_username")


    #     self.assertEqual(self.response.status_code, 200)
    #     self.assertEqual(result.count(), 0)
    #     self.assertEqual(search_username, None)



class StartChatTest(TestCase):
    def setUp(self):
        self.username1 = "testusername002"
        self.username = "testusername001"
        self.url = reverse("user", args=[self.username1])
        self.user1 = User.objects.create_user(username=self.username1, password="testuserpassword001")
        self.user = User.objects.create_user(username=self.username, password="testuserpassword001")

        self.client.login(username='testusername001', password="testuserpassword001")
        

    def test_start_chat(self):
        self.response = self.client.get(self.url)
        group = Group.objects.get()

        self.assertEqual(self.response.status_code, 302)
        self.assertEqual(self.response.url, reverse("group", args=[group.uuid]))

    def test_none_user(self):
        url = reverse("user", args=["noneuser"])
        self.response = self.client.get(url)

        self.assertEqual(self.response.status_code, 404)

    def test_redirect(self):
        url = reverse("user", args=[self.user.username])
        self.response = self.client.get(url)

        self.assertEqual(self.response.url, reverse("home"))

    def test_repeat_request(self):
        self.client.get(self.url)
        self.client.logout()
        self.client.login(username=self.username1, password="testuserpassword001")

        url = reverse("user", args=[self.username])

        response = self.client.get(url)
        group = Group.objects.all()
        self.assertEqual(group.count(), 1) # no new entries were created
        self.assertEqual(response.url, reverse("group", args=[group[0].uuid]))

    
class CreateGroupTest(TestCase):
    def setUp(self):
        self.url = reverse("create_group")

        self.user2 = User.objects.create_user(username="testusername003", password="testuserpassword001")
        self.user1 = User.objects.create_user(username="testusername002", password="testuserpassword001")
        self.user = User.objects.create_user(username='testusername001', password="testuserpassword001")

        gr1 = Group.objects.create()
        gr1.members.add(self.user, self.user1)

        gr2 = Group.objects.create()
        gr2.members.add(self.user, self.user2)

        self.client.login(username='testusername001', password="testuserpassword001")

    def test_connect_context(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "create_group.html")
        self.assertEqual(response.context.get("user"), self.user)

    def test_form_valid(self):
        name = "Cool girls"
        response = self.client.post(self.url, 
        {
            "name": name, 
            "members": [self.user1.id, self.user2.id], 
        })
        group = Group.objects.all().last()
        group_member = GroupMemberModel.objects.filter(group=group)

        self.assertEqual(response.url, reverse("home"))
        self.assertEqual(group.name, name)
        self.assertEqual(Event.objects.all().count(), 2)
        self.assertEqual(group_member.count(), 3)
        self.assertEqual(group.type, Group.GroupType.PUBLIC)
        self.assertTrue(group_member.filter(user=self.user).first().is_admin)
        self.assertFalse(group_member.filter(user=self.user1).first().is_admin)
        self.assertFalse(group_member.filter(user=self.user2).first().is_admin)
    
    def test_form_invalid(self):
        response = self.client.post(self.url, 
        {
            "name":  "Cool girls", 
            "members": [], 
        })
        self.assertTemplateUsed(response, "create_group.html")
        self.assertEqual(Group.objects.all().count(), 2)


class GroupInfoTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="test_user1", password="testuserpassword001")
        self.user2 = User.objects.create_user(username="test_user2", password="testuserpassword001")

        self.group1 = Group.objects.create(name="test_group")
        self.group1.members.add(self.user1, self.user2)

        self.client.login(username="test_user1", password="testuserpassword001")
        self.url = reverse("group-info", args=[self.group1.uuid])

    def test_context_data(self):
        response = self.client.get(self.url)
        group_members = GroupMemberModel.objects.filter(group=self.group1)
        current_groupmember = GroupMemberModel.objects.get(user=self.user1, group=self.group1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get("current_groupmember"), current_groupmember)
        self.assertEqual(list(response.context.get("members_info")), list(group_members))

    def test_assert_to_group_404(self):

        group = Group.objects.create()
        group.members.add(self.user2)

        url = reverse("group-info", args=[group.uuid])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class GroupEditTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="test_user1", password="testuserpassword001")
        self.user2 = User.objects.create_user(username="test_user2", password="testuserpassword001")
        
        self.group1 = Group.objects.create(name="test_group")
        self.group1.members.add(self.user2, self.user1)
        self.group1.type = Group.GroupType.PUBLIC
        self.group1.save()

        group_member_user = GroupMemberModel.objects.get(user=self.user1, group=self.group1)
        group_member_user.is_admin = True
        group_member_user.creator = True
        group_member_user.save()

        self.url = reverse("group-edit", args=[self.group1.uuid])

    def test_context_data(self):
        self.client.login(username="test_user1", password="testuserpassword001")
        response = self.client.get(self.url)

        group_members = GroupMemberModel.objects.filter(group=self.group1)
        current_groupmember = GroupMemberModel.objects.get(user=self.user1, group=self.group1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get("current_groupmember"), current_groupmember)
        self.assertEqual(list(response.context.get("members_info")), list(group_members))

    def test_assert_to_group_403(self):
        self.client.login(username="test_user2", password="testuserpassword001")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_form_kwargs(self):
        self.client.login(username="test_user1", password="testuserpassword001")
        user3 = User.objects.create_user(username="test_user3", password="testuserpassword001")
        
        group = Group.objects.create()
        group.members.add(user3, self.user1)

        response = self.client.get(self.url)
        form = response.context["form"]
        
        members = list(form.fields["members"].queryset)
        edit = form.fields["members"].required

        self.assertIn(user3, members) # Доступ добавления пользователей, с которыми был создан чат
        self.assertNotIn(self.user1, members)
        self.assertNotIn(self.user2, members)
        self.assertEqual(edit, False)

    def test_form_valid(self):
        self.client.login(username="test_user1", password="testuserpassword001")
        user3 = User.objects.create_user(username="test_user3", password="testuserpassword001")
        group = Group.objects.create()
        group.members.add(user3, self.user1)

        response = self.client.post(self.url,
            {
                "members": [user3.id], 
                "name":"new_name"
            } 
        )
        self.group1.refresh_from_db()

        print(Group.objects.get(uuid=self.group1.uuid).members)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.group1.name, "new_name")
        self.assertTrue(
            GroupMemberModel.objects.filter(
                group=self.group1,
                user=user3
            ).exists()
        )

        self.assertTrue(
            Event.objects.filter(
                group=self.group1,
                user=user3,
                type="Join"
            ).exists()
        )
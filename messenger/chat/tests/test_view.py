from django.test import TestCase
from chat.models import *
from django.urls import reverse

class ChatHomeViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="testusername002", password="testuserpassword001")
        self.user = User.objects.create_user(username='testusername001', password="testuserpassword001")

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
        self.assertEqual(groups[0][1], self.group)
        self.assertEqual(groups[0][0], self.user1.username)
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
        messages = self.response_uuid.context.get("messages")
        group_member = self.response_uuid.context.get("group_member")

        self.assertEqual(group_member, self.user1)
        self.assertEqual(self.group, group)
        self.assertEqual(messages[0].content, "hello!")
    
    def test_name_group(self):
        group = Group.objects.create(type=Group.GroupType.PUBLIC, name="cool girls")
        group.members.add(self.user, self.user1)
        response = self.client.get(self.url)
        
        groups = response.context.get("groups")
        self.assertIn(["cool girls", group], groups)


class AccountsSearchViewTest(TestCase):
    def setUp(self):
        self.url = reverse("search")
        self.user1 = User.objects.create_user(username="testusername002", password="testuserpassword001")
        self.user = User.objects.create_user(username='testusername001', password="testuserpassword001")

        self.client.login(username='testusername001', password="testuserpassword001")

    def test_context_full_username(self):
        self.response = self.client.get(self.url, {"search_user":self.user1.username})

        result = self.response.context.get("object_list")
        search_username = self.response.context.get("search_username")

        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result[0], self.user1)
        self.assertEqual(search_username, self.user1.username)
        self.assertTemplateUsed(self.response,"accounts.html")

    
    def test_context_part_username(self):
        self.response = self.client.get(self.url, {"search_user":self.user1.username[:1]})

        result = self.response.context.get("object_list")
        search_username = self.response.context.get("search_username")

        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(result.count(), 0)
        self.assertEqual(search_username, self.user1.username[:1])

    
    def test_context_logout(self):
        self.client.logout()
        self.response = self.client.get(self.url)

        self.assertEqual(self.response.status_code, 302)

    def test_context_none_searchuser(self):
        self.response = self.client.get(self.url)

        result = self.response.context.get("object_list")
        search_username = self.response.context.get("search_username")


        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(result.count(), 0)
        self.assertEqual(search_username, None)


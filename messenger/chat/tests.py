from django.test import TestCase
from .models import Group, Message, User, GroupMemberModel


class MessageModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="testusername001", password="testuserpassword001")
        self.user2 = User.objects.create_user(username="testusername002", password="testuserpassword002")

        self.group = Group.objects.create(name="testgroup")
        self.group.members.add(self.user1, self.user2)

        self.message = Message.objects.create(author=self.user1, content="testcontent", group=self.group)

    def test_create_user(self):
        return self.assertIsInstance(self.user1, User)

    def test_create_group(self):
        return self.assertIsInstance(self.group, Group)
    
    def test_create_groupmember(self):
        groupmember = len(GroupMemberModel.objects.filter(user=self.user1, group=self.group))
        return self.assertEqual(groupmember, 1)

    def test_get_absolute_url(self):
        return self.assertIsNotNone(self.group.get_absolute_url())

    def test_get_name_public(self):
        name = "pg"
        group_public = Group.objects.create(type=Group.GroupType.PUBLIC, name=name)
        group_public.members.add(self.user1, self.user2)
        return self.assertEqual(group_public.get_name(self.user1), name)

    def test_add_user_to_group_add(self):
        user = User.objects.create(username="testusername003", password="testuserpassword003")
        self.group.add_user_to_group(user)
        return self.assertIn(user, self.group.members.all())

    def test_remove_user_from_group(self):
        user = User.objects.create(username="testusername003", password="testuserpassword003")
        self.group.add_user_to_group(user)
        self.group.remove_user_from_group(user)
        return self.assertNotIn(user, self.group.members.all())
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
        return self.assertFalse(self.group.get_absolute_url() is None)
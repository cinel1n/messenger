from django.test import TestCase
from chat.form import GroupForm
from chat.models import User, Group
from django.urls import reverse


class GroupFormTest(TestCase):
    def setUp(self):
        url = reverse('create_group')
        self.user = User.objects.create_user(username="testusername001", password="testuserpassword001")
        self.user1 = User.objects.create_user(username="testusername002", password="testuserpassword001")

        self.group = Group.objects.create()
        self.group.members.add(self.user, self.user1)

        self.client.login(username='testusername001', password="testuserpassword001")
        self.response = self.client.get(url, )

        self.form = self.response.context.get("form") # get the form from the template context.


    def test_create_group_form(self):
        self.assertIsInstance(self.form, GroupForm)

    def test_group_members(self):
        queryset = self.form.fields["members"].queryset
        self.assertIn(self.user1, queryset)
        self.assertNotIn(self.user, queryset)

    def test_remove_user(self):
        self.group.remove_user_from_group(self.user) # remove admin from model
        form1 = GroupForm(user=self.user) # create a new form using the existing database objects
        queryset = form1.fields["members"].queryset
        self.assertEqual(queryset.count(), 0)

    def test_valid(self):
        group = GroupForm(
            data={
                "name": "TestValid", 
                "members":[self.user1.id, ], 
                }, 
            user=self.user
        )
        group1 = GroupForm(
            data={
                "name": "TestValid", 
                "members": [], 
                }, 
            user=self.user
        )
        group2 = GroupForm(
            data={
                "members":[self.user1.id, ], 
                }, 
            user=self.user
        )
        group3 = GroupForm(
            data={
                "name":"TestValid",
                "members":[self.user1.id, ], 
                }, 
        )
        self.assertTrue(group.is_valid())
        self.assertFalse(group1.is_valid())
        self.assertFalse(group2.is_valid())
        self.assertFalse(group3.is_valid())

    def test_distinct(self):
        self.group1 = Group.objects.create()
        self.group1.members.add(self.user, self.user1)
        
        self.assertEqual(self.form.fields["members"].queryset.count(), 1)
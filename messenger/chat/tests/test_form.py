from django.test import TestCase
from chat.form import GroupForm
from chat.models import User
from django.urls import reverse


class GroupFormTest(TestCase):
    def setUp(self):
        url = reverse('create_group')
        self.user = User.objects.create_user(username="testusername001", password="testuserpassword001")
        self.client.login(username='testusername001', password="testuserpassword001")
        self.response = self.client.get(url, )

    def test_create_group_form(self):
        # получаем форму из контекста, который мы передаем в шаблон
        form = self.response.context.get("form") 
        self.assertIsInstance(form, GroupForm)
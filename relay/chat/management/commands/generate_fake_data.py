from django.core.management.base import BaseCommand
from faker import Faker
from chat.models import Message, Group

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        fake = Faker('ru_RU') 
        group = Group.objects.get(uuid="7abc891a-80d4-473e-8df0-63a603c1a3a4")
        member1 = group.members.all()[0]
        member2 = group.members.all()[1]

        for _ in range(1000):
            Message.objects.create(group=group, content=fake.sentence(nb_words=6), author=member1)
            Message.objects.create(group=group, content=fake.sentence(nb_words=6), author=member2)
            

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена фейковыми данными!'))

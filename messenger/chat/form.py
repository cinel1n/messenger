from django import forms
from .models import Group
from login.models import User

class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name' ]

    def  __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.initial['first_name'] = user.first_name
            self.initial['last_name'] = user.last_name
            self.initial['username'] = user.username

class GroupForm(forms.ModelForm):
    name = forms.CharField(max_length=50, label="Название группы", widget=forms.TextInput(attrs={"class":"form-control"}))
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), 
        widget=forms.CheckboxSelectMultiple,
        required=True, 
        label="Участники"
    )

    class Meta:
        model = Group
        fields = ["name"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            groups = user.group_set.all()

            self.fields["members"].queryset = User.objects.filter(group__in=groups).exclude(id=user.id).distinct()
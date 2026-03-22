from django import forms
from .models import Group
from login.models import User

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
            self.fields["members"].queryset = User.objects.exclude(id=user.id)
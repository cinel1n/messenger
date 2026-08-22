from django import forms
from .models import Group
from login.models import User


class GroupForm(forms.ModelForm):
    name = forms.CharField(max_length=50, label="Name group", widget=forms.TextInput(attrs={"class":"form-control"}))
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), 
        widget=forms.CheckboxSelectMultiple,
        required=True, 
        label="Add members"
    )

    class Meta:
        model = Group
        fields = ["name",'avatar'] 

    def __init__(self, *args, members_queryset=None, edit=False, **kwargs):
        super().__init__(*args, **kwargs)
        if members_queryset:
            self.fields["members"].queryset = members_queryset
        if edit:
            self.fields["members"].required = False
            
            
        
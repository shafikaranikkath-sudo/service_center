from django import forms
from django.contrib.auth.models import User


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('Admin','Admin'),('Manager','Manager'),('Staff','Staff')])


    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

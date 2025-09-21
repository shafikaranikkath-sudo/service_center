from .models import UserProfile
from django import forms
from django.contrib.auth.models import User,Group
from django.contrib.auth.forms import PasswordChangeForm

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('Admin','Admin'),('Manager','Manager'),('Staff','Staff')])
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[('Admin', 'Admin'), ('Manager', 'Manager'), ('Staff', 'Staff')],
        required=False,
        help_text="Select the role for this user"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select current role
        if self.instance and self.instance.groups.exists():
            self.fields['role'].initial = self.instance.groups.first().name

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')

        if commit:
            user.save()
            if role:
                # Remove old groups and set new one
                user.groups.clear()
                group, created = Group.objects.get_or_create(name=role)
                user.groups.add(group)
        return user    

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfilePicForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_pic']
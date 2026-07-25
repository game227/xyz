"""Accounts forms.

Validation rule from the spec: every form gets frontend (HTML5 required/
type=email) AND backend validation (clean_* methods below) — never rely
on the browser alone.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser


class RegisterForm(UserCreationForm):
    """Public self-registration form. Role is always forced to STUDENT —
    admins are created via Django admin / createsuperuser only, never here.
    """
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, max_length=150, label='Ism')
    last_name = forms.CharField(required=True, max_length=150, label='Familiya')

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu email allaqachon ro\'yxatdan o\'tgan.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.STUDENT
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Login', widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label='Parol', widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'avatar', 'bio', 'specialty']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Specialty asosan o‘qituvchilar uchun; studentlarga ham ixtiyoriy bio ochiq
        if self.instance and not self.instance.can_manage_content:
            self.fields['specialty'].widget = forms.HiddenInput()

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu email boshqa foydalanuvchiga tegishli.')
        return email

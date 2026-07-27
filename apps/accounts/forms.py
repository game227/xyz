"""Accounts forms.

Validation rule from the spec: every form gets frontend (HTML5 required/
type=email) AND backend validation (clean_* methods below) — never rely
on the browser alone.
"""
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.validators import RegexValidator

from .models import CustomUser

phone_validator = RegexValidator(
    regex=r'^\+?998[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$|^$',
    message='Telefon +998 XX XXX XX XX formatida bo‘lsin (yoki bo‘sh qoldiring).',
)


class RegisterForm(UserCreationForm):
    """Public self-registration form. Role is always forced to STUDENT —
    admins are created via Django admin / createsuperuser only, never here.
    """
    email = forms.EmailField(required=True, label='Elektron pochta')
    first_name = forms.CharField(required=True, max_length=150, label='Ism')
    last_name = forms.CharField(required=True, max_length=150, label='Familiya')
    phone_number = forms.CharField(
        required=False,
        max_length=20,
        label='Telefon',
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+998 90 123 45 67'}),
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'phone_number', 'password1', 'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu elektron pochta allaqachon ro‘yxatdan o‘tgan.')
        return email

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return ''
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('998') and len(digits) == 12:
            return f'+{digits}'
        if len(digits) == 9:
            return f'+998{digits}'
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.STUDENT
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Login',
        widget=forms.TextInput(attrs={'autofocus': True}),
    )
    password = forms.CharField(label='Parol', widget=forms.PasswordInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'avatar',
            'bio', 'full_bio', 'education', 'achievements', 'telegram', 'specialty',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'full_bio': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].validators.append(phone_validator)
        if self.instance and not self.instance.can_manage_content:
            self.fields['specialty'].widget = forms.HiddenInput()

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Bu elektron pochta boshqa foydalanuvchiga tegishli.')
        return email

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if not phone:
            return ''
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('998') and len(digits) == 12:
            return f'+{digits}'
        if len(digits) == 9:
            return f'+998{digits}'
        return phone


class UzPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Elektron pochta')


class UzSetPasswordForm(SetPasswordForm):
    pass

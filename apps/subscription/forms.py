from django import forms
from django.core.validators import RegexValidator

from .constants import PLAN_DAYS_CHOICES


phone_validator = RegexValidator(
    regex=r'^\+?998[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$',
    message='Telefon +998 XX XXX XX XX formatida bo‘lsin.',
)


class SubscriptionRequestForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="To‘liq ism")
    phone = forms.CharField(
        max_length=30,
        label='Telefon',
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': '+998 90 123 45 67'}),
    )
    telegram = forms.CharField(
        max_length=120,
        required=False,
        label='Telegram',
        widget=forms.TextInput(attrs={'placeholder': '@username'}),
    )
    plan_days = forms.TypedChoiceField(
        choices=PLAN_DAYS_CHOICES,
        coerce=int,
        label='Tarif',
    )
    note = forms.CharField(
        required=False,
        label='Izoh',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ixtiyoriy xabar…'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                css = 'form-control'
                if name == 'plan_days':
                    css = 'form-select'
                field.widget.attrs['class'] = css
        if user and getattr(user, 'is_authenticated', False):
            self.fields['full_name'].initial = user.get_full_name() or user.username
            if user.phone_number:
                self.fields['phone'].initial = user.phone_number
            if getattr(user, 'telegram', None):
                self.fields['telegram'].initial = user.telegram

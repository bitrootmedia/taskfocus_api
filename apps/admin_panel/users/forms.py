from django import forms

from core.models import User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "image",
            "pushover_user",
            "notifier_user",
            "archived_at",
            "use_beacons",
            "teams",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "pushover_user": forms.TextInput(attrs={"class": "form-control"}),
            "notifier_user": forms.TextInput(attrs={"class": "form-control"}),
            "archived_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "teams": forms.SelectMultiple(attrs={"class": "form-select"}),
            "use_beacons": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teams"].required = False

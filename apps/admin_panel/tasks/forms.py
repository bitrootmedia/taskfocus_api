from django import forms

from core.models import Task, TaskAccess, User


class TaskForm(forms.ModelForm):
    permissions_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="User Access",
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "project",
            "tag",
            "position",
            "parent_task",
            "owner",
            "responsible",
            "is_closed",
            "progress",
            "eta_date",
            "estimated_work_hours",
            "is_urgent",
            "status",
            "urgency_level",
            "follow_up",
            "archived_at",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control"}),
            "tag": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.NumberInput(attrs={"class": "form-control"}),
            "progress": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100"}),
            "eta_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estimated_work_hours": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "follow_up": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "archived_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "urgency_level": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "responsible": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "parent_task": forms.Select(attrs={"class": "form-select"}),
            "is_closed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_urgent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "permissions_users": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prepopulate TaskAccess-based permissions
        if self.instance.pk:
            self.fields["permissions_users"].initial = User.objects.filter(tasks__task=self.instance)

    def save(self, commit=True):
        instance = super().save(commit=commit)

        # Sync TaskAccess records
        if instance.pk:
            selected_users = self.cleaned_data["permissions_users"]

            # Remove existing access for users not in selection
            TaskAccess.objects.filter(task=instance).exclude(user__in=selected_users).delete()

            # Add missing TaskAccess entries
            for user in selected_users:
                TaskAccess.objects.get_or_create(task=instance, user=user)

        return instance

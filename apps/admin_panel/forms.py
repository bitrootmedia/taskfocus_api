from django.forms import ModelForm

from core.models import Task, User


# User Form
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "is_active"]


# Task Form
class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "status"]

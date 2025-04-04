from django_tables2 import Table

from core.models import Task, User


# User Table
class UserTable(Table):
    class Meta:
        model = User
        fields = ("username", "email", "is_active")


# Task Table
class TaskTable(Table):
    class Meta:
        model = Task
        fields = ("title", "status")

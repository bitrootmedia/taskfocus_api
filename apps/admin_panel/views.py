from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django_tables2 import SingleTableView

from core.models import Task, User

from .forms import TaskForm, UserForm
from .tables import TaskTable, UserTable


# Task List View
class TaskListView(SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "admin_panel/task_list.html"


# User List View
class UserListView(SingleTableView):
    model = User
    table_class = UserTable
    template_name = "admin_panel/user_list.html"


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "admin_panel/task_form.html", {"form": form})


@login_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect("user_list")
    return render(request, "admin_panel/user_form.html", {"form": form})


@login_required
def admin_dashboard(request):
    return render(request, "admin_panel/dashboard.html")

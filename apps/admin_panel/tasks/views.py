from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView
from django_tables2.views import SingleTableView

from core.models import Task

from ..auth import StaffRequiredMixin
from .forms import TaskForm
from .tables import TaskTable


class TaskListView(StaffRequiredMixin, SingleTableView):
    model = Task
    table_class = TaskTable
    template_name = "admin_panel/tasks/task_list.html"


class TaskCreateView(StaffRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "admin_panel/tasks/task_form.html"
    success_url = reverse_lazy("task-list")


class TaskUpdateView(StaffRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "admin_panel/tasks/task_form.html"
    success_url = reverse_lazy("task-list")


class TaskDeleteView(StaffRequiredMixin, DeleteView):
    model = Task
    template_name = "admin_panel/tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task-list")

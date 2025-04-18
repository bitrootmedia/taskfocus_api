from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView
from django_tables2 import SingleTableView

from core.models import User

from ..auth import StaffRequiredMixin
from .forms import UserForm
from .tables import UserTable


class UserListView(StaffRequiredMixin, SingleTableView):
    model = User
    table_class = UserTable
    template_name = "admin_panel/users/user_list.html"


class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = "admin_panel/users/user_form.html"
    success_url = reverse_lazy("user-list")


class UserUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "admin_panel/users/user_form.html"
    success_url = reverse_lazy("user-list")


class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    template_name = "admin_panel/users/user_confirm_delete.html"
    success_url = reverse_lazy("user-list")

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .auth import StaffRequiredMixin


class AdminPanelHomeView(StaffRequiredMixin, TemplateView):
    template_name = "admin_panel/home.html"


def admin_panel_logout(request):
    logout(request)
    return redirect("admin-panel-home")

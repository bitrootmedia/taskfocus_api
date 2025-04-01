from django.views.generic import TemplateView

from .auth import StaffRequiredMixin


class AdminPanelHomeView(StaffRequiredMixin, TemplateView):
    template_name = "admin_panel/home.html"

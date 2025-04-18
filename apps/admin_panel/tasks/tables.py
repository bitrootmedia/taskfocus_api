import django_tables2 as tables

from core.models import Task


class TaskTable(tables.Table):
    permissions = tables.TemplateColumn(
        template_code="""
            {% for access in record.permissions.all %}
                <span class="badge bg-blue-lt">{{ access.user.username }}</span>
            {% empty %}
                <span class="text-muted">—</span>
            {% endfor %}
        """,
        verbose_name="Access",
        orderable=False,
    )

    actions = tables.TemplateColumn(
        template_name="admin_panel/tasks/task_actions_column.html", verbose_name="Actions", orderable=False
    )

    class Meta:
        model = Task
        template_name = "django_tables2/bootstrap4.html"
        fields = ("title", "status", "urgency_level", "owner", "responsible", "progress", "eta_date", "permissions")

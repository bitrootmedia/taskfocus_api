import django_tables2 as tables

from core.models import User


class UserTable(tables.Table):
    avatar = tables.TemplateColumn(
        template_code="""
            {% if record.image %}
                <img src="{{ record.image.url }}" width="32" height="32" class="rounded-circle" />
            {% else %}
                <span class="avatar avatar-rounded bg-secondary-lt">N/A</span>
            {% endif %}
        """,
        verbose_name="Avatar",
        orderable=False,
    )
    actions = tables.TemplateColumn(
        template_name="admin_panel/users/user_actions_column.html", orderable=False, verbose_name="Actions"
    )

    class Meta:
        model = User
        template_name = "django_tables2/bootstrap4.html"
        fields = ("username", "email", "avatar", "is_active", "use_beacons", "archived_at")

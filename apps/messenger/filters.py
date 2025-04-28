import django_filters
from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Message


class MessageFilter(filters.FilterSet):
    content = django_filters.CharFilter(lookup_expr="icontains")
    query = filters.CharFilter(method="filter_by_content")
    thread = django_filters.UUIDFilter(field_name="thread_id")
    sender = django_filters.UUIDFilter(field_name="sender_id")
    date_from = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_to = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Message
        fields = ["content", "thread", "sender", "date_from", "date_to", "query"]

    def filter_by_content(self, queryset, name, value):
        return queryset.filter(content__icontains=value)

import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 500

    def get_paginated_response(self, data):
        if self.request.query_params.get("page_size"):
            self.page_size = int(self.request.query_params.get("page_size"))

        total_page = math.ceil(self.page.paginator.count / self.page_size)

        return Response(
            {
                "count": self.page.paginator.count,
                "total": total_page,
                "page_size": self.page_size,
                "current": self.page.number,
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "results": data,
            }
        )

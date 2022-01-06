from rest_framework import pagination
from rest_framework.views import Response

class FollowListPagination(pagination.PageNumberPagination):
    page_size = 5

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,  # total objects count
            'next': self.get_next_page_num(),
            'previous': self.get_prev_page_num(),
            'results': data
        })


    def get_next_page_num(self):
        if not self.page.has_next():
            return None
        return self.page.next_page_number()

    def get_prev_page_num(self):
        if not self.page.has_previous():
            return None
        return self.page.previous_page_number()

"""Pagination that matches the shape called out in the assignment:

    {
        "next": "http://example.com/features/?page=3",
        "prev": "http://example.com/features/?page=1",
        "results": [<GeoJSON Feature Object>, ...]
    }

A strict GeoJSON FeatureCollection doesn't allow paging, so we return the
custom envelope but keep each `results` item a valid GeoJSON Feature.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FeatureCollectionPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data) -> Response:
        return Response({
            "type": "FeatureCollection",       # informational; not a strict FC
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "prev": self.get_previous_link(),
            "results": data,
        })

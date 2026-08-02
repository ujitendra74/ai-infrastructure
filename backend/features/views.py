from rest_framework import viewsets

from .filters import apply_feature_filters
from .models import Feature
from .serializers import FeatureSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    """CRUD for GeoJSON features.

    - GET   /api/features/          list (paginated, filterable by ?bbox=&name=)
    - POST  /api/features/          create
    - GET   /api/features/{id}/     retrieve
    - PUT   /api/features/{id}/     replace
    - PATCH /api/features/{id}/     partial update
    - DELETE/api/features/{id}/     delete

    Authentication: JWT (see settings.REST_FRAMEWORK).
    """

    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return apply_feature_filters(qs, self.request.query_params)

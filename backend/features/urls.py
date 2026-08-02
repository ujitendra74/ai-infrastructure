from rest_framework.routers import DefaultRouter

from .views import FeatureViewSet

router = DefaultRouter()
router.register(r"features", FeatureViewSet, basename="feature")

urlpatterns = router.urls

from django.urls import path

from .views import FeaturesView, MapView, home

urlpatterns = [
    path("", home, name="home"),
    path("map/", MapView.as_view(), name="map"),
    path("features/", FeaturesView.as_view(), name="features"),
]

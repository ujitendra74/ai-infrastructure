from django.shortcuts import redirect
from django.views.generic import TemplateView


class MapView(TemplateView):
    template_name = "frontend/map.html"


class FeaturesView(TemplateView):
    template_name = "frontend/features.html"


def home(request):
    return redirect("map")

from django.contrib.gis import admin

from .models import Feature


@admin.register(Feature)
class FeatureAdmin(admin.GISModelAdmin):
    list_display = ("id", "name", "color", "updated_at")
    search_fields = ("name",)

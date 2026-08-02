from django.contrib.gis.db import models


class Feature(models.Model):
    """A GeoJSON-compatible spatial feature stored in PostGIS.

    `name` and `color` are first-class columns because they are used for
    filtering/rendering. `properties` holds any additional free-form
    GeoJSON properties.
    """

    name = models.CharField(max_length=200, blank=True, default="")
    color = models.CharField(max_length=32, blank=True, default="#3388ff")
    properties = models.JSONField(default=dict, blank=True)

    # GeometryField accepts Point, LineString, Polygon, etc. — WGS84 (SRID 4326).
    geometry = models.GeometryField(srid=4326, spatial_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name or f"Feature #{self.pk}"

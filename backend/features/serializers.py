"""GeoJSON-compatible serializers for the Feature model.

We hand-roll the GeoJSON shape (rather than pulling in django-rest-framework-gis)
to keep the dependency surface small and to make the format explicit for review.
"""
import json

from django.contrib.gis.geos import GEOSGeometry, GEOSException
from rest_framework import serializers

from .models import Feature


class FeatureSerializer(serializers.ModelSerializer):
    """Serializes a Feature as a GeoJSON Feature object.

    Read shape:
        {
            "type": "Feature",
            "id": 1,
            "geometry": {"type": "Point", "coordinates": [4.9, 52.37]},
            "properties": {"name": "...", "color": "...", ...extra...}
        }

    Write shape: same, plus tolerant to updates that only send `properties`
    (PATCH from the edit page).
    """

    type = serializers.SerializerMethodField()
    geometry = serializers.JSONField(required=False)
    properties = serializers.JSONField(required=False)

    class Meta:
        model = Feature
        fields = ["type", "id", "geometry", "properties"]
        read_only_fields = ["id"]

    def get_type(self, _obj) -> str:
        return "Feature"

    # ---- read ----------------------------------------------------------

    def to_representation(self, instance: Feature) -> dict:
        geometry = json.loads(instance.geometry.geojson) if instance.geometry else None
        properties = dict(instance.properties or {})
        # Promote first-class columns into properties for GeoJSON consumers.
        properties.setdefault("name", instance.name)
        properties.setdefault("color", instance.color)
        return {
            "type": "Feature",
            "id": instance.id,
            "geometry": geometry,
            "properties": properties,
        }

    # ---- write ---------------------------------------------------------

    def _split_properties(self, properties: dict) -> tuple[str | None, str | None, dict]:
        """Extract `name` / `color` out of properties and return the rest."""
        properties = dict(properties or {})
        name = properties.pop("name", None)
        color = properties.pop("color", None)
        return name, color, properties

    def _parse_geometry(self, geometry) -> GEOSGeometry:
        if isinstance(geometry, dict):
            geometry = json.dumps(geometry)
        try:
            geom = GEOSGeometry(geometry)
        except (GEOSException, ValueError, TypeError) as exc:
            raise serializers.ValidationError({"geometry": f"Invalid GeoJSON geometry: {exc}"})
        if geom.srid is None:
            geom.srid = 4326
        return geom

    def create(self, validated_data: dict) -> Feature:
        geometry = validated_data.get("geometry")
        if geometry is None:
            raise serializers.ValidationError({"geometry": "This field is required."})

        name, color, extra = self._split_properties(validated_data.get("properties", {}))
        return Feature.objects.create(
            geometry=self._parse_geometry(geometry),
            name=name or "",
            color=color or "#3388ff",
            properties=extra,
        )

    def update(self, instance: Feature, validated_data: dict) -> Feature:
        if "geometry" in validated_data and validated_data["geometry"] is not None:
            instance.geometry = self._parse_geometry(validated_data["geometry"])

        if "properties" in validated_data:
            name, color, extra = self._split_properties(validated_data["properties"])
            if name is not None:
                instance.name = name
            if color is not None:
                instance.color = color
            # Merge extra properties rather than overwriting on PATCH.
            if self.partial:
                merged = dict(instance.properties or {})
                merged.update(extra)
                instance.properties = merged
            else:
                instance.properties = extra

        instance.save()
        return instance

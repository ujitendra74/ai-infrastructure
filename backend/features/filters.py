"""Query-parameter filters for the Feature list endpoint."""
from django.contrib.gis.geos import Polygon
from rest_framework.exceptions import ValidationError


def parse_bbox(bbox_str: str) -> Polygon:
    """Parse a `minLon,minLat,maxLon,maxLat` string into a WGS84 Polygon.

    Follows the GeoJSON/OGC bbox convention.
    """
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValidationError({"bbox": "Expected 4 comma-separated numbers: minLon,minLat,maxLon,maxLat"})
    try:
        min_lon, min_lat, max_lon, max_lat = (float(p) for p in parts)
    except ValueError as exc:
        raise ValidationError({"bbox": f"Non-numeric value in bbox: {exc}"})

    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValidationError({"bbox": "min values must be strictly less than max values"})

    return Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))


def apply_feature_filters(queryset, query_params):
    """Apply bbox / name filters coming from the request query string."""
    bbox = query_params.get("bbox")
    if bbox:
        polygon = parse_bbox(bbox)
        polygon.srid = 4326
        # `bboverlaps` uses the PostGIS && operator on the spatial index — fast.
        queryset = queryset.filter(geometry__bboverlaps=polygon)

    name = query_params.get("name")
    if name:
        queryset = queryset.filter(name__icontains=name)

    return queryset

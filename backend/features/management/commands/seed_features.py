"""Seed a handful of demo features so the map/edit pages have something to show.

Also creates an `admin/admin` superuser in DEBUG for convenience.
"""
import random

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from features.models import Feature

DEMO_CITIES = [
    ("Amsterdam", 4.9041, 52.3676, "#e63946"),
    ("Rotterdam", 4.4777, 51.9244, "#f1a208"),
    ("The Hague", 4.3007, 52.0705, "#2a9d8f"),
    ("Utrecht", 5.1214, 52.0907, "#3a86ff"),
    ("Eindhoven", 5.4697, 51.4416, "#8338ec"),
    ("Groningen", 6.5665, 53.2194, "#06d6a0"),
    ("Maastricht", 5.6889, 50.8514, "#ff006e"),
    ("Delft", 4.3571, 52.0116, "#118ab2"),
]


class Command(BaseCommand):
    help = "Create demo features (and an admin user in DEBUG)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=len(DEMO_CITIES),
                            help="How many features to create.")
        parser.add_argument("--wipe", action="store_true",
                            help="Delete existing features before seeding.")

    def handle(self, *args, **opts):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
            self.stdout.write(self.style.SUCCESS("Created superuser admin/admin"))

        if opts["wipe"]:
            deleted, _ = Feature.objects.all().delete()
            self.stdout.write(f"Wiped {deleted} existing features")

        count = opts["count"]
        rng = random.Random(42)
        created = 0
        for i in range(count):
            base = DEMO_CITIES[i % len(DEMO_CITIES)]
            name, lon, lat, color = base
            # jitter after the first pass so we get > len(DEMO_CITIES) points
            if i >= len(DEMO_CITIES):
                lon += rng.uniform(-0.05, 0.05)
                lat += rng.uniform(-0.05, 0.05)
                name = f"{name} #{i}"
            Feature.objects.create(
                name=name,
                color=color,
                properties={"seeded": True},
                geometry=Point(lon, lat, srid=4326),
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} features"))

"""End-to-end tests for the features API.

These require a spatial DB (PostGIS in prod, SpatiaLite for local `manage.py test`).
"""
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase

from .models import Feature


class FeatureApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user("tester", password="pw12345!")

    def setUp(self):
        # obtain a JWT and attach it to the client
        resp = self.client.post("/api/auth/token/", {"username": "tester", "password": "pw12345!"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    def test_requires_auth(self):
        self.client.credentials()  # drop token
        resp = self.client.get("/api/features/")
        self.assertEqual(resp.status_code, 401)

    def test_create_and_list(self):
        payload = {
            "geometry": {"type": "Point", "coordinates": [4.9, 52.37]},
            "properties": {"name": "A", "color": "#f00", "extra": 1},
        }
        resp = self.client.post("/api/features/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["type"], "Feature")
        self.assertEqual(resp.data["properties"]["name"], "A")
        self.assertEqual(resp.data["properties"]["extra"], 1)

        resp = self.client.get("/api/features/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertIn("results", resp.data)
        self.assertEqual(resp.data["results"][0]["type"], "Feature")

    def test_bbox_filter(self):
        Feature.objects.create(name="in", geometry=Point(5.0, 52.0, srid=4326))
        Feature.objects.create(name="out", geometry=Point(-5.0, -5.0, srid=4326))

        resp = self.client.get("/api/features/?bbox=4,51,6,53")
        self.assertEqual(resp.status_code, 200)
        names = [f["properties"]["name"] for f in resp.data["results"]]
        self.assertIn("in", names)
        self.assertNotIn("out", names)

    def test_patch_merges_properties(self):
        f = Feature.objects.create(name="orig", color="#000",
                                   properties={"keep": True},
                                   geometry=Point(0, 0, srid=4326))
        resp = self.client.patch(f"/api/features/{f.id}/",
                                 {"properties": {"name": "new", "added": 1}},
                                 format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        f.refresh_from_db()
        self.assertEqual(f.name, "new")
        self.assertEqual(f.properties, {"keep": True, "added": 1})

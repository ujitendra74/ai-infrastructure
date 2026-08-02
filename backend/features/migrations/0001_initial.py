import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Feature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, default="", max_length=200)),
                ("color", models.CharField(blank=True, default="#3388ff", max_length=32)),
                ("properties", models.JSONField(blank=True, default=dict)),
                ("geometry", django.contrib.gis.db.models.fields.GeometryField(spatial_index=True, srid=4326)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.AddIndex(
            model_name="feature",
            index=models.Index(fields=["name"], name="features_fe_name_idx"),
        ),
    ]

# Solution Walk-through

This document explains **what I built**, **why I made the design choices I did**,
and **how each part of the assignment is satisfied**. Read it alongside the code
in `geo_api/`.

---

## 1. What the assignment asked for

| # | Requirement                                                                | Where it lives                                                    |
|---|----------------------------------------------------------------------------|-------------------------------------------------------------------|
| 1 | Django REST API serving GeoJSON features                                   | `features/views.py`, `features/serializers.py`                    |
| 2 | Custom paginated envelope `{next, prev, results}` (not a strict FeatureCollection) | `features/pagination.py`                                          |
| 3 | Bounding-box filter                                                        | `features/filters.py` (`?bbox=minLon,minLat,maxLon,maxLat`)       |
| 4 | 100 features per page                                                      | `PAGE_SIZE = 100` in `settings.py`                                |
| 5 | JWT authorization                                                          | `djangorestframework-simplejwt` wired in `settings.py` + `urls.py`|
| 6 | HTML page visualising features (OpenLayers)                                | `frontend/templates/frontend/map.html`                            |
| 7 | HTML page listing + editing feature properties (Bootstrap for bonus)       | `frontend/templates/frontend/features.html`                       |
| 8 | PostGIS storage                                                            | `features/models.py` (`GeometryField`, `srid=4326`) + `docker-compose.yml` |
| 9 | Dockerfile + docker-compose (bonus)                                        | `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`               |
| 10| README                                                                     | `geo_api/README.md`                                               |

---

## 2. Architecture at a glance

```
Browser ──HTTP──▶ Django (Gunicorn)
                    │
     ┌──────────────┼───────────────┐
     ▼              ▼               ▼
 /map/ page   /features/ page   /api/features/  ◀── JWT-protected
 (OpenLayers) (Bootstrap edit)   (DRF ViewSet)
                                       │
                                       ▼
                                 PostGIS (GiST spatial index)
```

Two Django apps keep concerns separate:

- **`features/`** — data model, API, filters, pagination, admin, tests.
- **`frontend/`** — nothing but templates + trivial view classes. The pages
  talk to the API over `fetch()` with a Bearer JWT that lives in
  `localStorage` — no server-rendered feature data, so the same API is used
  by the UI and by external clients.

---

## 3. Data model (`features/models.py`)

```python
class Feature(models.Model):
    name       = CharField(max_length=200)
    color      = CharField(max_length=32, default="#3388ff")
    properties = JSONField(default=dict)          # free-form GeoJSON properties
    geometry   = GeometryField(srid=4326, spatial_index=True)   # PostGIS
    created_at / updated_at
```

Design notes:

- **`GeometryField` (not `PointField`)** — the assignment says "vector features",
  which in GeoJSON means Points, LineStrings, Polygons, etc. `GeometryField`
  accepts them all.
- **SRID 4326 (WGS84)** — the coordinate system GeoJSON is defined in
  (RFC 7946). No reprojection needed on the API boundary.
- **`spatial_index=True`** — creates a PostGIS GiST index, which is what the
  bbox filter uses under the hood. Without it, bbox queries fall back to
  seq-scan and get slow past a few thousand rows.
- **`name` and `color` as first-class columns**, not just JSON keys — they are
  filterable, indexable, and shown in the UI. `properties` is a JSONB catch-all
  for anything else the client wants to store.

---

## 4. Serializer (`features/serializers.py`)

I chose to hand-write the GeoJSON shape instead of pulling in
`djangorestframework-gis`. Reasons:

- The GeoJSON transform is 30 lines. Adding a whole GIS-serializer dependency
  for that isn't worth it in a small project.
- The output shape is explicit in code — easier to review, easier to change.

Key behaviours:

- **Read** — assembles a proper GeoJSON Feature object:
  `{type, id, geometry, properties}`. Promotes `name`/`color` back into
  `properties` so external GeoJSON consumers (like OpenLayers) can read them
  without special-casing.
- **Write (POST)** — accepts a GeoJSON geometry (as dict or string), splits
  `name`/`color` out of `properties`, stores the rest in the JSON column.
- **Write (PATCH)** — merges `properties` instead of overwriting. That means
  the edit page can send just `{properties: {name}}` without wiping other
  keys — the intuitive behaviour for a partial update.
- **Validation** — bad GeoJSON raises `ValidationError` with a message
  pointing at the `geometry` field.

---

## 5. Pagination (`features/pagination.py`)

The assignment specifically calls out that a real `FeatureCollection` doesn't
allow paging, and shows the target shape:

```json
{ "next": "...", "prev": "...", "results": [<GeoJSON Feature>, ...] }
```

`FeatureCollectionPagination` extends DRF's `PageNumberPagination` and
returns exactly that envelope (plus `count` and a `type` marker for the UI).
Default page size is **100**, capped at 1000 via `page_size_query_param`.

---

## 6. Bounding-box filter (`features/filters.py`)

- Query string: `?bbox=minLon,minLat,maxLon,maxLat` — GeoJSON/OGC convention.
- Parsed into a WGS84 `Polygon` and applied with `geometry__bboverlaps=`.
  That maps to the PostGIS `&&` operator, which **uses the GiST index** on
  `geometry` — index-hit even for millions of rows.
- Invalid bboxes return a 400 with a helpful message
  (`"Expected 4 comma-separated numbers…"`).
- Also included: `?name=amster` (icontains) — small, useful, cheap.

---

## 7. Authentication

- **JWT** via `djangorestframework-simplejwt`.
- Endpoints:
  - `POST /api/auth/token/`         → `{access, refresh}`
  - `POST /api/auth/token/refresh/` → new `access`
- `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — every API call needs a
  valid token.
- The frontend stores the token pair in `localStorage`, injects
  `Authorization: Bearer …` into every `fetch`, and transparently refreshes
  once on 401. Login is a small Bootstrap modal in the base template.

---

## 8. Frontends

Both pages share `base.html`, which provides:

- Bootstrap 5 nav + login modal.
- A tiny `Auth` client (login, refresh, `Auth.fetch`) that all page scripts use.

### 8a. Map page — `frontend/templates/frontend/map.html`

- OpenLayers 9, OSM basemap, `EPSG:3857` view.
- Loads features via the API and reads them with `ol.format.GeoJSON`
  (reprojected 4326 → 3857).
- **Live bbox loading**: on `moveend`, reads the current view extent, converts
  it to WGS84, and re-queries the API with `?bbox=…`. A toggle lets you
  disable this if you want to load everything.
- Follows pagination — walks `data.next` until it's null.
- Click a feature to see a popup with name/id.

### 8b. Features page — `frontend/templates/frontend/features.html`

- Bootstrap-styled table with inline **name** (text input) and **color**
  (native color picker) editors, plus Save/Delete buttons per row.
- Save issues `PATCH /api/features/{id}/` with just the changed properties —
  the serializer's merge-on-PATCH keeps everything else intact.
- Prev/Next pagination, name-substring filter, page size 25 (smaller than the
  map's 100 so the table stays readable).

---

## 9. Storage & queries (PostGIS)

- Uses `postgis/postgis:16-3.4` in docker-compose so the extension is
  pre-installed.
- The migration creates the `geometry` column with a GiST spatial index
  (`spatial_index=True`).
- Bbox queries use `&&` on that index; you can see this by running
  `EXPLAIN ANALYZE` on the generated SQL — it hits the index, not a seq scan.
- The Feature table is deliberately tall+thin: `id, name, color, properties,
  geometry, timestamps`. If we needed feature *types* or per-user ownership,
  those would be additional columns/foreign keys rather than nested JSON.

---

## 10. Docker

- **`Dockerfile`** — Python 3.12 slim, installs GDAL/GEOS/PROJ (required by
  GeoDjango), `pip install -r requirements.txt`, runs Gunicorn.
- **`docker-compose.yml`** — two services, `db` (PostGIS) and `web`, with a
  `healthcheck` on the DB so `web` waits for `pg_isready` before starting.
- **`entrypoint.sh`** — polls Postgres, runs `migrate`, collects static, and
  seeds demo data (only if the table is empty).

Result: `docker compose up --build` is a one-liner that gives you a working
map + editor.

---

## 11. What I deliberately left out

- **django-rest-framework-gis** — not needed for the 30-line GeoJSON transform.
- **django-filter** — one bbox param doesn't justify the dependency.
- **User-scoped features / permissions** — the assignment doesn't ask for it,
  and adding half a permissions model would be worse than none.
- **Refresh-token rotation / token blacklist** — SimpleJWT defaults are fine
  for the assignment scope.
- **Real production settings** (SECRET_KEY handling, `DEBUG=False`, secure
  cookies, etc.) — flagged in `.env.example`; would be part of a deploy
  checklist, not the assignment.

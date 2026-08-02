# Geo API — Django + PostGIS + GeoJSON

A small Django REST API that serves vector features in a GeoJSON-compatible
format, with bounding-box filtering, JWT auth, and two HTML frontends
(OpenLayers map + Bootstrap edit page).

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

Then open:

- Map:      http://localhost:8000/map/
- Features: http://localhost:8000/features/
- Admin:    http://localhost:8000/admin/  (admin / admin)

The first boot seeds a superuser (`admin` / `admin`) and a handful of demo
features so the map has something to show.

## Quick start (local, without Docker)

Requires Python 3.12+ and a PostGIS-enabled Postgres (or SpatiaLite).

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # then edit DB_* to point at your DB
python manage.py migrate
python manage.py seed_features
python manage.py runserver
```

## API

All API endpoints require a Bearer JWT.

```bash
# 1. get a token
curl -X POST http://localhost:8000/api/auth/token/ \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"admin"}'
# → {"access":"...","refresh":"..."}

TOKEN=...

# 2. list features (paginated, 100/page)
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/features/?bbox=4,51,6,53&page_size=100"

# 3. create
curl -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -X POST http://localhost:8000/api/features/ \
     -d '{"geometry":{"type":"Point","coordinates":[4.9,52.37]},"properties":{"name":"Amsterdam","color":"#e63946"}}'

# 4. partial update
curl -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -X PATCH http://localhost:8000/api/features/1/ \
     -d '{"properties":{"name":"Amsterdam Centraal"}}'
```

### List response shape

Matches the shape described in the assignment:

```json
{
  "type": "FeatureCollection",
  "count": 250,
  "next": "http://localhost:8000/api/features/?page=3",
  "prev": "http://localhost:8000/api/features/?page=1",
  "results": [
    {
      "type": "Feature",
      "id": 42,
      "geometry": {"type": "Point", "coordinates": [4.9, 52.37]},
      "properties": {"name": "Amsterdam", "color": "#e63946"}
    }
  ]
}
```

### Query params on `/api/features/`

| Param       | Example                          | Notes |
|-------------|----------------------------------|-------|
| `bbox`      | `4,51,6,53`                      | `minLon,minLat,maxLon,maxLat` (WGS84) |
| `name`      | `amster`                         | case-insensitive substring match |
| `page`      | `2`                              | page number (1-based)               |
| `page_size` | `50`                             | up to 1000; default 100             |

## Tests

```bash
python manage.py test
```

## Project layout

```
backend/
├── config/            # settings, top-level urls, wsgi/asgi
├── features/          # model, serializer, pagination, filter, viewset, admin, tests
├── frontend/          # templates (map + features pages)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

See `EXPLANATION.md` for a walk-through of the design decisions.

#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres to be reachable before running migrations.
if [ -n "${DB_HOST:-}" ]; then
  echo "Waiting for database at ${DB_HOST}:${DB_PORT:-5432}..."
  for i in $(seq 1 60); do
    if pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER:-geo}" >/dev/null 2>&1; then
      echo "Database is ready."
      break
    fi
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# Seed on first boot if the table is empty.
python manage.py shell -c "
from features.models import Feature
import sys
sys.exit(0 if Feature.objects.exists() else 1)
" || python manage.py seed_features

exec "$@"

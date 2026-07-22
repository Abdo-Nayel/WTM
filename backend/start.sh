#!/bin/sh
set -e

cd /app

echo "[WorkTaskMe] migrate..."
python manage.py migrate --noinput

echo "[WorkTaskMe] collectstatic..."
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-False}" = "True" ] || [ "${SEED_DEMO:-false}" = "true" ]; then
  echo "[WorkTaskMe] seed_demo..."
  python manage.py seed_demo || true
fi

PORT="${PORT:-8000}"
echo "[WorkTaskMe] starting Daphne on 0.0.0.0:${PORT}"
exec daphne -b 0.0.0.0 -p "${PORT}" config.asgi:application

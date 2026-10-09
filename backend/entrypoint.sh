#!/bin/sh
set -e

# Si el repo aún no incluye migraciones de la app, se generan y se imprimen en los logs
# para poder copiarlas al repositorio (así quedan versionadas).
if ! ls portfolio/migrations/0001_*.py >/dev/null 2>&1; then
  echo "=== makemigrations: no hay migraciones versionadas, generando ==="
  python manage.py makemigrations portfolio --noinput
  for f in portfolio/migrations/0*.py; do
    echo "=== BEGIN $f ==="
    cat "$f"
    echo "=== END $f ==="
  done
fi

python manage.py migrate --noinput
python manage.py bootstrap

exec gunicorn config.wsgi:application \
  --bind "[::]:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile -

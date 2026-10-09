# Portfolio · Joswen

Portfolio de diseñador gráfico con una escena 3D en la portada y un mini admin para subir el trabajo.

- **`frontend/`** — [Astro](https://astro.build) (SSR con adaptador Node). Hero 3D con Three.js: un anillo de pósters impresos que se alimenta con las portadas de los proyectos.
- **`backend/`** — Django + [Wagtail](https://wagtail.org) como mini admin y API JSON de solo lectura. Postgres en producción; imágenes en un bucket S3 de Railway.

```
Visitante ──▶ frontend (Astro SSR) ──(red privada)──▶ backend (Wagtail /api/*)
                                                         │        │
                                                    Postgres   Bucket S3 (privado)
Visitante ──▶ backend /media/*  (proxy con caché inmutable hacia el bucket)
Tú ─────────▶ backend /admin/   (subir proyectos e imágenes)
```

## Estructura del sitio

| Página | Contenido |
| --- | --- |
| `/` | Hero 3D · Trabajo seleccionado · Servicios · Sobre mí + marcas · Contacto |
| `/work` | Todos los proyectos, con filtro por categoría |
| `/work/<slug>` | Ficha: datos, portada, descripción, galería (ancho completo / media columna) y siguiente proyecto |

Todo el texto (titulares, «Sobre mí», contacto, redes, color de acento) y el contenido (proyectos, servicios) se edita en el admin. Los textos por defecto son de ejemplo: cámbialos.

## El admin (`/admin/`)

- **Proyectos** — título, categoría, año, cliente, rol, resumen, descripción, portada, galería con orden y disposición, destacado, publicado y orden.
- **Servicios** — lista de servicios de la portada.
- **Imágenes** — biblioteca de Wagtail (se guardan en el bucket). Se admiten JPG, PNG, WebP, AVIF y GIF hasta 30 MB.
- **Ajustes → Ajustes del sitio** — textos, contacto, redes, color de acento y URL de Spline.

Las imágenes se sirven en WebP con varios tamaños. Los cambios aparecen en la web en unos segundos, sin volver a desplegar.

## 3D

La escena integrada (`frontend/src/scripts/scene.js`) respeta `prefers-reduced-motion` (imagen estática) y se pausa cuando el hero no está a la vista.

Para usar una escena propia de [Spline](https://spline.design): publícala, copia la URL `.splinecode` (Export → Code → Viewer) y pégala en **Ajustes del sitio → URL de escena Spline**. Se mostrará en la portada en lugar de los pósters.

## Variables de entorno

### Backend

| Variable | Valor |
| --- | --- |
| `SECRET_KEY` | Cadena aleatoria larga |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `PORT` | `8000` |
| `AWS_S3_BUCKET_NAME` | `${{<Bucket>.BUCKET}}` |
| `AWS_S3_ENDPOINT_URL` | `${{<Bucket>.ENDPOINT}}` |
| `AWS_ACCESS_KEY_ID` | `${{<Bucket>.ACCESS_KEY_ID}}` |
| `AWS_SECRET_ACCESS_KEY` | `${{<Bucket>.SECRET_ACCESS_KEY}}` |
| `AWS_S3_REGION_NAME` | `${{<Bucket>.REGION}}` |
| `PUBLIC_BASE_URL` | URL pública del backend (si no se define se usa `RAILWAY_PUBLIC_DOMAIN`) |
| `DJANGO_SUPERUSER_USERNAME` / `_PASSWORD` / `_EMAIL` | Crea el administrador en el primer arranque |
| `SEED_DEMO` | `1` para cargar proyectos de muestra si no hay ninguno (opcional) |

### Frontend

| Variable | Valor |
| --- | --- |
| `BACKEND_URL` | `http://<servicio-backend>.railway.internal:8000` |

Sin variables, el backend funciona en local con SQLite y disco.

## Desarrollo local

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DEBUG=1
python manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=admin SEED_DEMO=1 python manage.py bootstrap
python manage.py runserver            # http://localhost:8000/admin/

# Frontend (otra terminal)
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev   # http://localhost:4321
```

## Despliegue en Railway

Proyecto con tres servicios y un bucket:

1. **Postgres** — plantilla oficial de Railway.
2. **Bucket** — almacenamiento S3 de Railway (privado; el backend lo expone en `/media/` con caché).
3. **backend** — este repo, *Root Directory* `/backend` (Dockerfile), healthcheck `/api/health/`. Ejecuta migraciones y `bootstrap` en cada arranque.
4. **frontend** — este repo, *Root Directory* `/frontend` (Dockerfile), healthcheck `/healthz`.

Cada `git push` a la rama principal redespliega ambos servicios.

"""API JSON de solo lectura que consume el frontend Astro."""
from urllib.parse import urljoin

from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET
from wagtail.rich_text import expand_db_html

from .models import Project, Service, SiteSettings

THUMB_WIDTHS = (480, 960, 1600, 2400)


def _abs(url):
    return urljoin(settings.PUBLIC_BASE_URL + "/", url)


def image_payload(image, alt=""):
    """Serializa una imagen de Wagtail con srcset en WebP."""
    if image is None:
        return None
    widths = [w for w in THUMB_WIDTHS if w < image.width]
    renditions = [(w, image.get_rendition(f"width-{w}|format-webp")) for w in widths]
    # La mayor resolución: si la original es menor que el siguiente ancho, se usa tal cual (en WebP).
    largest_w = min(image.width, THUMB_WIDTHS[-1])
    if not renditions or renditions[-1][0] != largest_w:
        renditions.append((largest_w, image.get_rendition(f"width-{largest_w}|format-webp")))

    srcset = ", ".join(f"{_abs(r.url)} {w}w" for w, r in renditions)
    default = renditions[min(2, len(renditions) - 1)][1]
    return {
        "id": image.pk,
        "alt": alt or image.title,
        "width": image.width,
        "height": image.height,
        "src": _abs(default.url),
        "srcset": srcset,
        "thumb": _abs(renditions[0][1].url),
        "medium": _abs(renditions[min(1, len(renditions) - 1)][1].url),
    }


def project_card(project):
    return {
        "slug": project.slug,
        "title": project.title,
        "category": project.category,
        "year": project.year,
        "client": project.client,
        "summary": project.summary,
        "featured": project.featured,
        "cover": image_payload(project.cover, project.title),
    }


def project_detail(project):
    data = project_card(project)
    data.update(
        {
            "role": project.role,
            "description": expand_db_html(project.description) if project.description else "",
            "gallery": [
                {
                    "caption": item.caption,
                    "layout": item.layout,
                    "image": image_payload(item.image, item.caption or project.title),
                }
                for item in project.gallery.select_related("image").all()
            ],
        }
    )
    return data


def _json(payload):
    response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    response["Cache-Control"] = "public, max-age=15"
    return response


def _published():
    return Project.objects.filter(published=True).select_related("cover")


@require_GET
def site(request):
    cfg = SiteSettings.load()
    clients = [line.strip() for line in cfg.clients_list.splitlines() if line.strip()]
    featured = list(_published().filter(featured=True)[:6]) or list(_published()[:6])
    return _json(
        {
            "settings": {
                "name": cfg.name,
                "role_line": cfg.role_line,
                "location": cfg.location,
                "hero_title": cfg.hero_title,
                "hero_subtitle": cfg.hero_subtitle,
                "availability_text": cfg.availability_text,
                "about_title": cfg.about_title,
                "about_text": expand_db_html(cfg.about_text),
                "portrait": image_payload(cfg.portrait, cfg.name),
                "contact_title": cfg.contact_title,
                "contact_text": cfg.contact_text,
                "email": cfg.email,
                "instagram": cfg.instagram,
                "behance": cfg.behance,
                "dribbble": cfg.dribbble,
                "linkedin": cfg.linkedin,
                "spline_url": cfg.spline_url,
                "accent_color": cfg.accent_color,
            },
            "clients": clients,
            "services": [
                {"title": s.title, "description": s.description} for s in Service.objects.all()
            ],
            "featured": [project_card(p) for p in featured],
        }
    )


@require_GET
def projects(request):
    items = [project_card(p) for p in _published()]
    categories = sorted({p["category"] for p in items if p["category"]})
    return _json({"projects": items, "categories": categories})


@require_GET
def project(request, slug):
    queryset = list(_published())
    for index, item in enumerate(queryset):
        if item.slug == slug:
            data = project_detail(item)
            nxt = queryset[(index + 1) % len(queryset)] if len(queryset) > 1 else None
            data["next"] = project_card(nxt) if nxt else None
            return _json(data)
    raise Http404()

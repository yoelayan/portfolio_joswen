import mimetypes

from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.http import require_GET

# Solo se exponen las carpetas que usa Wagtail para imágenes.
ALLOWED_PREFIXES = ("original_images/", "images/")


def health(request):
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def media_proxy(request, path):
    if ".." in path or not path.startswith(ALLOWED_PREFIXES):
        raise Http404()
    try:
        if not default_storage.exists(path):
            raise Http404()
        handle = default_storage.open(path, "rb")
    except (SuspiciousOperation, FileNotFoundError):
        raise Http404()

    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    response = FileResponse(handle, content_type=content_type)
    # Los nombres de fichero de Wagtail (originales y renditions) son únicos y no mutan.
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["Access-Control-Allow-Origin"] = "*"
    return response

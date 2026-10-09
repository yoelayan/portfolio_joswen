from django.urls import include, path, re_path
from django.views.generic import RedirectView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

from portfolio.views import media_proxy

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("api/", include("portfolio.urls")),
    re_path(r"^media/(?P<path>.+)$", media_proxy, name="media"),
    # Wagtail necesita su resolvedor de páginas registrado aunque el sitio sea "headless".
    path("_pages/", include(wagtail_urls)),
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
]

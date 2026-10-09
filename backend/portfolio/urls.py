from django.urls import path

from . import api, views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("site/", api.site, name="api-site"),
    path("projects/", api.projects, name="api-projects"),
    path("projects/<slug:slug>/", api.project, name="api-project"),
]

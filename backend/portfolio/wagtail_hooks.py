from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Project, Service


class ProjectViewSet(SnippetViewSet):
    model = Project
    icon = "image"
    menu_label = "Proyectos"
    menu_name = "proyectos"
    menu_order = 100
    add_to_admin_menu = True
    list_display = ["title", "category", "year", "featured", "published", "sort_order"]
    list_filter = ["category", "featured", "published"]
    search_fields = ["title", "client", "category"]


class ServiceViewSet(SnippetViewSet):
    model = Service
    icon = "list-ul"
    menu_label = "Servicios"
    menu_name = "servicios"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["title", "sort_order"]


register_snippet(ProjectViewSet)
register_snippet(ServiceViewSet)


@hooks.register("construct_main_menu")
def simplify_menu(request, menu_items):
    """Admin mínimo: se ocultan el árbol de páginas, informes y ayuda."""
    hidden = {"explorer", "reports", "help"}
    menu_items[:] = [item for item in menu_items if item.name not in hidden]

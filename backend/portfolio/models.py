from django.db import models
from django.utils.text import slugify
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.models import Orderable

RICH_FEATURES = ["bold", "italic", "link", "ol", "ul"]


@register_setting(icon="cog")
class SiteSettings(BaseGenericSetting):
    """Textos y enlaces globales del sitio. Todo editable desde el admin."""

    # Identidad
    name = models.CharField("Nombre", max_length=80, default="Joswen")
    role_line = models.CharField(
        "Profesión (línea corta)", max_length=120, default="Diseñador gráfico & director de arte"
    )
    location = models.CharField("Ubicación", max_length=120, blank=True, default="Remoto · Mundo")

    # Hero
    hero_title = models.CharField(
        "Título principal",
        max_length=200,
        default="Diseño que se mueve, se siente y se recuerda.",
    )
    hero_subtitle = models.TextField(
        "Subtítulo",
        default=(
            "Soy Joswen, diseñador gráfico. Construyo identidades, piezas editoriales y "
            "universos visuales para marcas que quieren verse como el futuro."
        ),
    )
    availability_text = models.CharField(
        "Texto de disponibilidad",
        max_length=160,
        blank=True,
        default="Disponible para nuevos proyectos",
    )

    # Sobre mí
    about_title = models.CharField(
        "Título «Sobre mí»",
        max_length=200,
        default="Detrás de cada pieza, una obsesión por el detalle.",
    )
    about_text = RichTextField(
        "Texto «Sobre mí»",
        features=RICH_FEATURES,
        default=(
            "<p>Trabajo en la intersección entre la estrategia de marca y la expresión visual. "
            "Cada proyecto empieza escuchando y termina en un sistema de identidad coherente, "
            "memorable y listo para vivir en cualquier soporte.</p>"
            "<p>Colaboro con estudios, startups y marcas personales que buscan una dirección "
            "creativa con carácter propio.</p>"
        ),
    )
    portrait = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Retrato / imagen «Sobre mí»",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    clients_list = models.TextField(
        "Marcas / clientes (una por línea)",
        blank=True,
        default="Nébula Studio\nAtlas Coffee\nOrbita\nLumen\nPulso Records\nTerra Wines",
        help_text="Se muestran en la cinta animada.",
    )

    # Contacto
    contact_title = models.CharField(
        "Título de contacto", max_length=200, default="¿Tienes una idea? Hagámosla inolvidable."
    )
    contact_text = models.TextField(
        "Texto de contacto",
        blank=True,
        default="Cuéntame qué necesitas y te respondo en menos de 48 horas.",
    )
    email = models.EmailField("Email", default="hola@joswen.com")
    instagram = models.URLField("Instagram", blank=True)
    behance = models.URLField("Behance", blank=True)
    dribbble = models.URLField("Dribbble", blank=True)
    linkedin = models.URLField("LinkedIn", blank=True)

    # 3D
    spline_url = models.URLField(
        "URL de escena Spline (opcional)",
        blank=True,
        help_text=(
            "Pega aquí la URL «.splinecode» de una escena publicada en Spline "
            "(Export → Code → Viewer). Si se deja vacío se usa la escena 3D integrada."
        ),
    )
    accent_color = models.CharField(
        "Color de acento", max_length=7, default="#ff5a1f", help_text="Hexadecimal, p. ej. #ff5a1f. Elige un tono vivo y claro: el texto sobre él es azul marino."
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("role_line"), FieldPanel("location")],
            heading="Identidad",
        ),
        MultiFieldPanel(
            [FieldPanel("hero_title"), FieldPanel("hero_subtitle"), FieldPanel("availability_text")],
            heading="Portada (hero)",
        ),
        MultiFieldPanel(
            [
                FieldPanel("about_title"),
                FieldPanel("about_text"),
                FieldPanel("portrait"),
                FieldPanel("clients_list"),
            ],
            heading="Sobre mí",
        ),
        MultiFieldPanel(
            [
                FieldPanel("contact_title"),
                FieldPanel("contact_text"),
                FieldPanel("email"),
                FieldPanel("instagram"),
                FieldPanel("behance"),
                FieldPanel("dribbble"),
                FieldPanel("linkedin"),
            ],
            heading="Contacto y redes",
        ),
        MultiFieldPanel(
            [FieldPanel("accent_color"), FieldPanel("spline_url")],
            heading="Apariencia y 3D",
        ),
    ]

    class Meta:
        verbose_name = "Ajustes del sitio"
        verbose_name_plural = "Ajustes del sitio"


class Service(models.Model):
    title = models.CharField("Servicio", max_length=100)
    description = models.TextField("Descripción", blank=True)
    sort_order = models.PositiveIntegerField("Orden", default=0)

    panels = [FieldPanel("title"), FieldPanel("description"), FieldPanel("sort_order")]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return self.title


class Project(ClusterableModel):
    title = models.CharField("Título", max_length=160)
    slug = models.SlugField(
        "Slug (URL)",
        max_length=180,
        unique=True,
        blank=True,
        help_text="Se genera solo a partir del título si lo dejas vacío.",
    )
    category = models.CharField(
        "Categoría",
        max_length=80,
        blank=True,
        help_text="p. ej. Branding, Editorial, Packaging, Motion",
    )
    year = models.PositiveSmallIntegerField("Año", null=True, blank=True)
    client = models.CharField("Cliente", max_length=120, blank=True)
    role = models.CharField("Mi rol", max_length=160, blank=True, help_text="p. ej. Identidad visual, Dirección de arte")
    summary = models.TextField("Resumen corto (tarjeta)", blank=True, max_length=300)
    description = RichTextField("Descripción del proyecto", features=RICH_FEATURES, blank=True)
    cover = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name="Imagen de portada",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    featured = models.BooleanField("Destacado en portada", default=False)
    published = models.BooleanField("Publicado", default=True)
    sort_order = models.PositiveIntegerField(
        "Orden", default=0, help_text="Números menores aparecen primero."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel("title"),
        FieldRowPanel([FieldPanel("category"), FieldPanel("year")]),
        FieldRowPanel([FieldPanel("client"), FieldPanel("role")]),
        FieldPanel("cover"),
        FieldPanel("summary"),
        FieldPanel("description"),
        InlinePanel("gallery", label="Imagen de la galería"),
        MultiFieldPanel(
            [
                FieldPanel("published"),
                FieldPanel("featured"),
                FieldPanel("sort_order"),
                FieldPanel("slug"),
            ],
            heading="Publicación",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "-year", "-id"]
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "proyecto"
            slug, n = base, 2
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ProjectImage(Orderable):
    LAYOUTS = [("full", "Ancho completo"), ("half", "Media columna")]

    project = ParentalKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ForeignKey(
        "wagtailimages.Image", verbose_name="Imagen", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField("Pie de foto", max_length=200, blank=True)
    layout = models.CharField("Disposición", max_length=10, choices=LAYOUTS, default="full")

    panels = [FieldPanel("image"), FieldPanel("caption"), FieldPanel("layout")]

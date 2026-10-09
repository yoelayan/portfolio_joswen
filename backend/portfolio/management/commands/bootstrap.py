"""
Preparación idempotente que se ejecuta en cada arranque del contenedor:

- crea el superusuario si DJANGO_SUPERUSER_USERNAME / _PASSWORD están definidos,
- asegura que existan los ajustes del sitio,
- carga datos demo (con imágenes generadas) si SEED_DEMO=1 y aún no hay proyectos.
"""
import os
import random
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image as PILImage
from PIL import ImageDraw
from wagtail.images import get_image_model

from portfolio.models import Project, ProjectImage, Service, SiteSettings

PALETTES = [
    ((20, 20, 40), (212, 255, 58)),
    ((255, 94, 58), (40, 10, 60)),
    ((10, 40, 90), (120, 220, 255)),
    ((30, 30, 30), (255, 255, 255)),
    ((90, 20, 120), (255, 160, 200)),
    ((10, 80, 60), (240, 255, 150)),
]

SERVICES = [
    ("Identidad de marca", "Logotipo, sistema visual y guía de uso para marcas con carácter."),
    ("Dirección de arte", "Conceptos y lenguaje visual coherentes para campañas y lanzamientos."),
    ("Diseño editorial", "Libros, revistas y piezas impresas con jerarquía y ritmo."),
    ("Packaging", "Envases que se ven bien en el estante y mejor en la mano."),
    ("Motion & 3D", "Piezas animadas y escenas 3D para redes, web y presentaciones."),
    ("Diseño web", "Sitios y landings con identidad propia, rápidos y expresivos."),
]

PROJECTS = [
    ("Nébula Studio", "Branding", 2026, "Nébula Studio", "Identidad visual y dirección de arte",
     "Sistema de identidad para un estudio creativo con alma espacial."),
    ("Atlas Coffee", "Packaging", 2025, "Atlas Coffee Co.", "Packaging y branding",
     "Línea de empaques para café de especialidad con ilustración cartográfica."),
    ("Pulso — Revista", "Editorial", 2025, "Pulso Records", "Diseño editorial",
     "Revista impresa sobre cultura sonora, con tipografía expresiva."),
    ("Lumen", "Motion", 2024, "Lumen", "Motion graphics y 3D",
     "Piezas animadas para el lanzamiento de una marca de iluminación."),
]


def make_art(width, height, palette, seed):
    rng = random.Random(seed)
    c1, c2 = palette
    base = PILImage.new("RGB", (width, height), c1)
    top = PILImage.new("RGB", (width, height), c2)
    mask = PILImage.linear_gradient("L").rotate(rng.choice([0, 90, 180, 270]), expand=True)
    mask = mask.resize((width, height))
    art = PILImage.composite(top, base, mask)
    draw = ImageDraw.Draw(art, "RGBA")
    for _ in range(rng.randint(3, 6)):
        r = rng.randint(min(width, height) // 8, min(width, height) // 2)
        x, y = rng.randint(0, width), rng.randint(0, height)
        color = rng.choice([c1, c2, (255, 255, 255)]) + (rng.randint(50, 160),)
        if rng.random() < 0.5:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        else:
            draw.rectangle([x - r, y - r // 2, x + r, y + r // 2], outline=color, width=max(2, width // 150))
    for i in range(rng.randint(4, 10)):
        y = int(height * i / 10)
        draw.line([(0, y), (width, y)], fill=(255, 255, 255, 40), width=1)
    return art


class Command(BaseCommand):
    help = "Prepara superusuario, ajustes iniciales y (opcional) datos demo."

    def handle(self, *args, **options):
        self._superuser()
        SiteSettings.load()
        if not Service.objects.exists():
            for order, (title, description) in enumerate(SERVICES):
                Service.objects.create(title=title, description=description, sort_order=order)
            self.stdout.write("Servicios iniciales creados.")
        if os.environ.get("SEED_DEMO", "").lower() in {"1", "true", "yes"} and not Project.objects.exists():
            self._seed_projects()

    def _superuser(self):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not username or not password:
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return
        User.objects.create_superuser(
            username=username,
            password=password,
            email=os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
        )
        self.stdout.write(f"Superusuario «{username}» creado.")

    def _image(self, title, width, height, palette, seed):
        Image = get_image_model()
        buffer = BytesIO()
        make_art(width, height, palette, seed).save(buffer, "JPEG", quality=86)
        buffer.seek(0)
        return Image.objects.create(
            title=title, file=ImageFile(buffer, name=f"{slugify(title)}-{seed}.jpg")
        )

    def _seed_projects(self):
        self.stdout.write("Cargando proyectos demo…")
        for index, (title, category, year, client, role, summary) in enumerate(PROJECTS):
            palette = PALETTES[index % len(PALETTES)]
            project = Project(
                title=title,
                category=category,
                year=year,
                client=client,
                role=role,
                summary=summary,
                description=f"<p>{summary} Proyecto de muestra: sustitúyelo por tu trabajo real desde el admin.</p>",
                featured=index < 3,
                published=True,
                sort_order=index,
                cover=self._image(f"{title} portada", 1600, 2000, palette, index * 10),
            )
            project.save()
            for n in range(3):
                ProjectImage.objects.create(
                    project=project,
                    image=self._image(
                        f"{title} {n + 1}",
                        2000,
                        1250 if n != 1 else 1600,
                        PALETTES[(index + n + 1) % len(PALETTES)],
                        index * 10 + n + 1,
                    ),
                    layout="full" if n == 0 else "half",
                    caption="",
                    sort_order=n,
                )
        self.stdout.write("Proyectos demo creados.")

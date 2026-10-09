from urllib.parse import quote

from django.conf import settings
from storages.backends.s3 import S3Storage


class BucketStorage(S3Storage):
    """
    Storage S3 para el bucket (privado) de Railway.

    Los buckets de Railway no son públicos, así que en vez de URLs firmadas
    (que caducan y rompen la caché) devolvemos URLs estables que apuntan a la
    vista proxy `/media/...` del backend, que lee del bucket y responde con
    cabeceras de caché inmutables.
    """

    def url(self, name, parameters=None, expire=None, http_method=None):
        return f"{settings.MEDIA_URL}{quote(str(name).lstrip('/'))}"

"""Almacenamiento privado para archivos que nunca deben servirse públicamente."""

from django.core.files.storage import FileSystemStorage


class PrivateFileSystemStorage(FileSystemStorage):
    """Evita que Django genere URLs públicas para archivos sensibles.

    Los archivos se guardan en PRIVATE_MEDIA_ROOT y solo se leen desde el
    servidor (por ejemplo, para incrustarlos como data URI en un HTML firmado
    por un usuario autenticado).
    """

    def url(self, name):
        raise ValueError("Los archivos privados no tienen URL pública.")

    def get_available_name(self, name, max_length=None):
        # Mantener nombres predecibles no es necesario; delegamos en Django.
        return super().get_available_name(name, max_length=max_length)

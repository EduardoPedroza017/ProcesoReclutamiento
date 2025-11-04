"""
Configuración de la app Documents
"""
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """
    Configuración para la app de Documents
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Gestión de Documentos'
    
    def ready(self):
        """
        Importa las señales cuando la app esté lista
        """
        # Importar señales si las hay
        # import apps.documents.signals
        pass
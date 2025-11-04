"""
Configuración de la app de Evaluations
"""

from django.apps import AppConfig


class EvaluationsConfig(AppConfig):
    """
    Configuración de la aplicación de evaluaciones
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.evaluations'
    verbose_name = 'Sistema de Evaluaciones'
    
    def ready(self):
        """
        Importar señales y configuraciones cuando la app esté lista
        """
        # Aquí se pueden importar signals si se necesitan
        # import apps.evaluations.signals
        pass
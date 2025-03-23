from django.apps import AppConfig


class LlmServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'llm_services'
    
    def ready(self):
        """
        Import signals when the app is ready
        This ensures that our property update signals are registered
        """
        import llm_services.signals

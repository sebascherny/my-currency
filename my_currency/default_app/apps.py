from django.apps import AppConfig


class DefaultAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "default_app"

    def ready(self):
        import default_app.signals

from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'

    def ready(self):
        import security.firebase  # 👈 Runs when Django starts

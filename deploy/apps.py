from django.apps import AppConfig


class DeployConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'deploy'

    def ready(self) -> None:
        import deploy.signals
        return super().ready()

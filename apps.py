from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        # imported here (not at module load time) so Django's app
        # registry is fully populated before the signal receivers below
        # touch other apps' models.
        from . import signals  # noqa: F401

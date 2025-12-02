from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'
    # Keep primary keys consistent with existing migrations (which use AutoField)
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import users.signals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='auditfinding',
            old_name='check',
            new_name='audit_check',
        ),
    ]

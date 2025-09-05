from django.db import migrations


def promote_default_admin(apps, schema_editor):
    User = apps.get_model("core", "User")
    try:
        u = User.objects.get(email__iexact="admin@example.com")
        u.role = "admin"
        u.is_staff = True
        u.is_superuser = False
        u.save(update_fields=["role", "is_staff", "is_superuser"])
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_user_role"),
    ]

    operations = [
        migrations.RunPython(promote_default_admin, migrations.RunPython.noop),
    ]

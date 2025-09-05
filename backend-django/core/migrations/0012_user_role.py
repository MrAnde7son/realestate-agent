from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_analytics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                max_length=20,
                choices=[("admin", "Admin"), ("member", "Member")],
                default="member",
                db_index=True,
            ),
        ),
    ]

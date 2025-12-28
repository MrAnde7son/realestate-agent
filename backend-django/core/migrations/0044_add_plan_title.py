from django.db import migrations, models


def populate_plan_titles(apps, schema_editor):
    Plan = apps.get_model("core", "Plan")

    for plan in Plan.objects.all().iterator():
        raw = plan.raw if isinstance(plan.raw, dict) else {}

        title = (
            raw.get("title")
            or raw.get("planTitle")
            or raw.get("planName")
            or raw.get("plan_name")
            or raw.get("mahut")
            or raw.get("name")
            or plan.description
            or plan.plan_number
        )

        if title and plan.title != title:
            plan.title = title
            plan.save(update_fields=["title"])


def noop_reverse(apps, schema_editor):
    """No-op reverse migration."""


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_m2m_links_and_listings"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="title",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(populate_plan_titles, noop_reverse),
    ]

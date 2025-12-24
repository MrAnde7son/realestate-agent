# Generated manually to update document types only

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_remove_planning_metrics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="document_type",
            field=models.CharField(
                choices=[
                    ("appraisal", "Appraisal"),
                    ("appraisal_decisive", "Decisive Appraisal"),
                    ("appraisal_rmi", "RAMI Appraisal"),
                    ("permit", "Building Permit"),
                    ("permit_construction", "Construction Permit"),
                    ("permit_renovation", "Renovation Permit"),
                    ("plan", "Planning Document"),
                    ("plan_local", "Local Plan"),
                    ("plan_citywide", "Citywide Plan"),
                    ("plan_detailed", "Detailed Plan"),
                    ("tabu", "Tabu"),
                    ("deed", "Deed"),
                    ("contract", "Contract"),
                    ("rights", "Rights Document"),
                    ("condo_plan", "Condominium Plan"),
                    ("blueprint", "Blueprint"),
                    ("architectural_drawing", "Architectural Drawing"),
                    ("technical_drawing", "Technical Drawing"),
                    ("other", "Other"),
                ],
                default="other",
                help_text="Type of document",
                max_length=50,
            ),
        ),
    ]

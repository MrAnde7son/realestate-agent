# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0052_add_api_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="openai_api_key",
            field=models.TextField(
                blank=True, help_text="User's OpenAI API key", null=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="gemini_api_key",
            field=models.TextField(
                blank=True, help_text="User's Gemini/Google API key", null=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="groq_api_key",
            field=models.TextField(
                blank=True, help_text="User's Groq API key", null=True
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="llm_provider_preference",
            field=models.CharField(
                blank=True,
                choices=[("openai", "OpenAI"), ("gemini", "Gemini"), ("groq", "Groq")],
                help_text="User's preferred LLM provider for the agent",
                max_length=20,
                null=True,
            ),
        ),
    ]

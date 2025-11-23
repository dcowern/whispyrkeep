from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("llm_config", "0002_alter_llmendpointconfig_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="llmendpointconfig",
            name="provider_name",
            field=models.CharField(
                choices=[
                    ("openai", "OpenAI"),
                    ("azure-openai", "Azure OpenAI"),
                    ("anthropic", "Anthropic"),
                    ("meta", "Meta (Llama)"),
                    ("mistral", "Mistral"),
                    ("google", "Google"),
                    ("custom", "Custom/Local"),
                    ("local", "Local/Legacy"),
                ],
                max_length=50,
            ),
        ),
    ]

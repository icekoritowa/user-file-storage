from django.db import migrations, models

import library.models


def populate_slugs(apps, schema_editor):
    folder = apps.get_model("library", "Folder")
    for item in folder.objects.filter(slug__isnull=True).iterator():
        item.slug = f"folder-{item.pk}"
        item.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0003_alter_file_options_alter_folder_options_and_more"),
    ]
    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="folder", name="slug",
            field=models.SlugField(default=library.models.folder_slug,
                                   max_length=64, unique=True,
                                   verbose_name="Адрес"),
        ),
    ]

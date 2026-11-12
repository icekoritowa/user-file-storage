from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='file',
            index=models.Index(fields=['folder', '-uploaded_at', 'id'], name='file_folder_date_idx'),
        ),
        migrations.AddIndex(
            model_name='file',
            index=models.Index(fields=['-size', 'id'], name='file_size_id_idx'),
        ),
    ]

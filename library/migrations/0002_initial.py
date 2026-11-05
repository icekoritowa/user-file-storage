import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('library', '0001_initial'),
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='members',
            field=models.ManyToManyField(related_name='shared_folders', through='permissions.Access', to='library.user'),
        ),
        migrations.AddField(
            model_name='folder',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='folders', to='library.user'),
        ),
        migrations.AddConstraint(
            model_name='file',
            constraint=models.UniqueConstraint(fields=('folder', 'name'), name='unique_folder_file'),
        ),
        migrations.AddConstraint(
            model_name='folder',
            constraint=models.UniqueConstraint(fields=('owner', 'name'), name='unique_owner_folder'),
        ),
    ]

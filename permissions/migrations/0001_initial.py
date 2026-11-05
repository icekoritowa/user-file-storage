import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Access',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('read', 'Чтение'), ('write', 'Чтение и запись')], default='read', max_length=5)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='library.folder')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='library.user')),
            ],
            options={
                'ordering': ['folder_id', 'user_id'],
                'constraints': [models.UniqueConstraint(fields=('user', 'folder'), name='unique_user_folder_access'), models.CheckConstraint(condition=models.Q(('level__in', ['read', 'write'])), name='valid_access_level')],
            },
        ),
    ]

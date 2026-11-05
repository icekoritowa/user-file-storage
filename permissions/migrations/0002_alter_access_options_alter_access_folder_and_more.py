import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0003_alter_file_options_alter_folder_options_and_more'),
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='access',
            options={'ordering': ['folder_id', 'user_id'], 'verbose_name': 'Право доступа', 'verbose_name_plural': 'Права доступа'},
        ),
        migrations.AlterField(
            model_name='access',
            name='folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='library.folder', verbose_name='Папка'),
        ),
        migrations.AlterField(
            model_name='access',
            name='level',
            field=models.CharField(choices=[('read', 'Чтение'), ('write', 'Чтение и запись')], default='read', max_length=5, verbose_name='Уровень'),
        ),
        migrations.AlterField(
            model_name='access',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accesses', to='library.user', verbose_name='Получатель'),
        ),
    ]

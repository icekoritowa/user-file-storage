import datetime
import django.db.models.deletion
import library.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_initial'),
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'ordering': ['id'], 'verbose_name': 'Файл', 'verbose_name_plural': 'Файлы'},
        ),
        migrations.AlterModelOptions(
            name='folder',
            options={'ordering': ['id'], 'verbose_name': 'Папка', 'verbose_name_plural': 'Папки'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['id'], 'verbose_name': 'Пользователь каталога', 'verbose_name_plural': 'Пользователи каталога'},
        ),
        migrations.AddField(
            model_name='file',
            name='is_large',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(size__gte=10485760, then=models.Value(True)), default=models.Value(False)), output_field=models.BooleanField(), verbose_name='Крупный файл'),
        ),
        migrations.AddField(
            model_name='folder',
            name='slug',
            field=models.SlugField(blank=True, max_length=64, null=True, unique=True, verbose_name='Адрес'),
        ),
        migrations.AlterField(
            model_name='file',
            name='folder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='files', to='library.folder', verbose_name='Папка'),
        ),
        migrations.AlterField(
            model_name='file',
            name='name',
            field=models.CharField(max_length=255, validators=[library.models.validate_name], verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='file',
            name='size',
            field=models.PositiveBigIntegerField(default=0, verbose_name='Размер, байт'),
        ),
        migrations.AlterField(
            model_name='file',
            name='uploaded_at',
            field=models.DateField(default=datetime.date.today, verbose_name='Дата загрузки'),
        ),
        migrations.AlterField(
            model_name='folder',
            name='members',
            field=models.ManyToManyField(related_name='shared_folders', through='permissions.Access', to='library.user', verbose_name='Получатели доступа'),
        ),
        migrations.AlterField(
            model_name='folder',
            name='name',
            field=models.CharField(max_length=255, validators=[library.models.validate_name], verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='folder',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='folders', to='library.user', verbose_name='Владелец'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Электронная почта'),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=255, validators=[library.models.validate_name], verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='user',
            name='quota',
            field=models.PositiveBigIntegerField(default=104857600, verbose_name='Квота, байт'),
        ),
    ]

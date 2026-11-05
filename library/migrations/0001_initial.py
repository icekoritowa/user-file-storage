import datetime
import django.db.models.deletion
import django.db.models.functions.text
import library.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, validators=[library.models.validate_name])),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, validators=[library.models.validate_name])),
                ('size', models.PositiveBigIntegerField(default=0)),
                ('uploaded_at', models.DateField(default=datetime.date.today)),
                ('folder', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='files', to='library.folder')),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, validators=[library.models.validate_name])),
                ('quota', models.PositiveBigIntegerField(default=104857600)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={
                'ordering': ['id'],
                'abstract': False,
                'constraints': [models.UniqueConstraint(django.db.models.functions.text.Lower('name'), name='unique_user_name')],
            },
        ),
    ]

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from db.database import connect, load_database
from file_storage.persistence import to_data
from library.models import File, Folder, User
from permissions.models import Access


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path,
                            default=settings.STORAGE_DATABASE)
        parser.add_argument("--if-empty", action="store_true")

    def handle(self, *args, **options):
        source = options["source"]
        if source.resolve() == Path(
            settings.DATABASES["default"]["NAME"],
        ).resolve():
            raise CommandError("Источник и целевая база должны различаться.")
        with transaction.atomic():
            if any(m.objects.exists() for m in (User, Folder, File, Access)):
                if options["if_empty"]:
                    self.stdout.write("В базе уже есть данные.")
                    return
                raise CommandError("Перенос разрешён только в пустую базу.")
            try:
                payload = to_data(load_database(source))
                with connect(source, readonly=True) as connection:
                    emails = dict(connection.execute(
                        "SELECT id, email FROM users"))
                for row in payload["users"]:
                    user = User(**row, email=emails[row["id"]])
                    user.full_clean()
                    user.save()
                for model, key in ((Folder, "folders"), (File, "files"),
                                   (Access, "accesses")):
                    for row in payload[key]:
                        obj = model(**row)
                        obj.full_clean()
                        obj.save()
            except Exception as error:
                raise CommandError(f"Ошибка переноса: {error}") from error
        self.stdout.write("Данные перенесены с сохранением ID и связей.")

from django.core.exceptions import ValidationError
from django.db import models


class AccessQuerySet(models.QuerySet):
    def readable(self):
        return self.filter(level=Access.Level.READ)

    def writable(self):
        return self.filter(level=Access.Level.WRITE)

    def with_names(self):
        return self.select_related("user", "folder__owner")


class Access(models.Model):
    class Level(models.TextChoices):
        READ = "read", "Чтение"
        WRITE = "write", "Чтение и запись"

    objects = AccessQuerySet.as_manager()

    user = models.ForeignKey("library.User", on_delete=models.CASCADE,
                             related_name="accesses",
                             verbose_name="Получатель")
    folder = models.ForeignKey("library.Folder", on_delete=models.CASCADE,
                               related_name="accesses", verbose_name="Папка")
    level = models.CharField("Уровень", max_length=5,
                             choices=Level.choices, default=Level.READ)

    class Meta:
        verbose_name = "Право доступа"
        verbose_name_plural = "Права доступа"
        ordering = ["folder_id", "user_id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "folder"],
                                    name="unique_user_folder_access"),
            models.CheckConstraint(condition=models.Q(level__in=[
                "read", "write",
            ]), name="valid_access_level"),
        ]

    def __str__(self):
        return f"{self.user} — {self.folder}: {self.level}"

    def clean(self):
        super().clean()
        if self.folder_id and self.user_id == self.folder.owner_id:
            raise ValidationError("Владельцу не нужно отдельное право.")

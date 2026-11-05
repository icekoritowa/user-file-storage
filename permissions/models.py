from django.core.exceptions import ValidationError
from django.db import models


class Access(models.Model):
    user = models.ForeignKey("library.User", on_delete=models.CASCADE,
                             related_name="accesses")
    folder = models.ForeignKey("library.Folder", on_delete=models.CASCADE,
                               related_name="accesses")
    level = models.CharField(max_length=5, choices=[
        ("read", "Чтение"), ("write", "Чтение и запись"),
    ], default="read")

    class Meta:
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

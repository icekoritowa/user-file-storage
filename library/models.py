from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from file_storage.validation import valid_name


def validate_name(value):
    try:
        if valid_name(value) != value:
            raise ValueError("Уберите пробелы по краям имени.")
    except ValueError as error:
        raise ValidationError(str(error)) from error


class NamedEntity(models.Model):
    name = models.CharField(max_length=255, validators=[validate_name])

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.name


class User(NamedEntity):
    quota = models.PositiveBigIntegerField(default=104857600)
    email = models.EmailField(null=True, blank=True)

    class Meta(NamedEntity.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_user_name"),
        ]


class Folder(NamedEntity):
    owner = models.ForeignKey(User, on_delete=models.PROTECT,
                              related_name="folders")
    members = models.ManyToManyField(User, through="permissions.Access",
                                     related_name="shared_folders")

    class Meta(NamedEntity.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"],
                                    name="unique_owner_folder"),
        ]


class File(NamedEntity):
    folder = models.ForeignKey(Folder, on_delete=models.PROTECT,
                               related_name="files")
    size = models.PositiveBigIntegerField(default=0)
    uploaded_at = models.DateField(default=date.today)

    class Meta(NamedEntity.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["folder", "name"],
                                    name="unique_folder_file"),
        ]

    def clean(self):
        super().clean()
        if self.folder_id and self.size is not None:
            used = File.objects.filter(
                folder__owner_id=self.folder.owner_id,
            ).exclude(pk=self.pk).aggregate(total=models.Sum("size"))["total"]
            if (used or 0) + self.size > self.folder.owner.quota:
                raise ValidationError({"size": "Превышена квота владельца."})

from datetime import date
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse

from file_storage.validation import valid_name


def folder_slug():
    return "folder-" + uuid4().hex


def validate_name(value):
    try:
        if valid_name(value) != value:
            raise ValueError("Уберите пробелы по краям имени.")
    except ValueError as error:
        raise ValidationError(str(error)) from error


class NamedEntity(models.Model):
    name = models.CharField("Название", max_length=255,
                            validators=[validate_name])

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.name


class User(NamedEntity):
    quota = models.PositiveBigIntegerField("Квота, байт", default=104857600)
    email = models.EmailField("Электронная почта", null=True, blank=True)

    class Meta(NamedEntity.Meta):
        abstract = False
        verbose_name = "Пользователь каталога"
        verbose_name_plural = "Пользователи каталога"
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_user_name"),
        ]

    def clean(self):
        super().clean()
        if self.pk and self.quota is not None:
            used = File.objects.filter(folder__owner=self).aggregate(
                total=models.Sum("size", default=0),
            )["total"]
            if self.quota < used:
                raise ValidationError({
                    "quota": "Квота меньше занятого места.",
                })


class Folder(NamedEntity):
    slug = models.SlugField("Адрес", max_length=64, unique=True,
                            default=folder_slug)

    def get_absolute_url(self):
        return reverse("library:folder_slug", kwargs={"slug": self.slug})

    owner = models.ForeignKey(User, on_delete=models.PROTECT,
                              related_name="folders", verbose_name="Владелец")
    members = models.ManyToManyField(User, through="permissions.Access",
                                     related_name="shared_folders",
                                     verbose_name="Получатели доступа")

    class Meta(NamedEntity.Meta):
        abstract = False
        verbose_name = "Папка"
        verbose_name_plural = "Папки"
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"],
                                    name="unique_owner_folder"),
        ]


class FileQuerySet(models.QuerySet):
    def nonempty(self):
        return self.exclude(size=0)

    def with_owners(self):
        return self.select_related("folder__owner")

    def uploaded_before(self, value):
        return self.filter(uploaded_at__lte=value)


class File(NamedEntity):
    objects = FileQuerySet.as_manager()
    is_large = models.GeneratedField(
        verbose_name="Крупный файл",
        expression=models.Case(
            models.When(size__gte=10485760, then=models.Value(True)),
            default=models.Value(False),
        ),
        output_field=models.BooleanField(), db_persist=True,
    )
    folder = models.ForeignKey(Folder, on_delete=models.PROTECT,
                               related_name="files", verbose_name="Папка")
    size = models.PositiveBigIntegerField("Размер, байт", default=0)
    uploaded_at = models.DateField("Дата загрузки", default=date.today)

    class Meta(NamedEntity.Meta):
        abstract = False
        verbose_name = "Файл"
        verbose_name_plural = "Файлы"
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

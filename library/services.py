from django.core.exceptions import PermissionDenied
from django.db import transaction

from library.models import File, User
from permissions.models import Access


def allowed(folder, actor_id, write=False):
    if folder.owner_id == actor_id:
        return True
    rights = Access.objects.filter(folder=folder, user_id=actor_id)
    if write:
        rights = rights.writable()
    return rights.exists()


@transaction.atomic
def save_file(file, actor_id):
    User.objects.select_for_update().get(pk=file.folder.owner_id)
    if not allowed(file.folder, actor_id, write=True):
        raise PermissionDenied("Нет права записи.")
    if file.pk:
        old = File.objects.select_related("folder").get(pk=file.pk)
        if not allowed(old.folder, actor_id, write=True):
            raise PermissionDenied("Нет права записи в исходную папку.")
    file.full_clean()
    file.save()
    return file


@transaction.atomic
def delete_file(file_id, actor_id):
    file = File.objects.select_related("folder").get(pk=file_id)
    if not allowed(file.folder, actor_id, write=True):
        raise PermissionDenied("Нет права удаления.")
    file.delete()


@transaction.atomic
def set_access(folder, user, level, actor_id):
    if folder.owner_id != actor_id:
        raise PermissionDenied("Доступом управляет владелец.")
    if level == "none":
        Access.objects.filter(folder=folder, user=user).delete()
        return
    access = Access.objects.filter(folder=folder, user=user).first()
    if access is None:
        access = Access(folder=folder, user=user)
    access.level = level
    access.full_clean()
    access.save()

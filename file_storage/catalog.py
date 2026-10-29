from __future__ import annotations

from collections.abc import Iterator

from .models import Access, File, Folder, NamedEntity, User
from .validation import nonnegative, positive_id, valid_name

COLLECTIONS = ("users", "folders", "files", "accesses")
Catalog = dict[str, list]


def empty_catalog() -> Catalog:
    return {name: [] for name in COLLECTIONS}


def get_record(data: Catalog, collection: str,
               record_id: int) -> NamedEntity:
    positive_id(record_id)
    for record in data[collection]:
        if record.id == record_id:
            return record
    raise ValueError(f"Не найден ID {record_id} в {collection}.")


def next_id(records: list[NamedEntity]) -> int:
    return max((record.id for record in records), default=0) + 1


def add_user(data: Catalog, name: str, quota: int) -> User:
    name = valid_name(name)
    if any(user.name.casefold() == name.casefold() for user in data["users"]):
        raise ValueError("Пользователь с таким именем уже существует.")
    user = User(next_id(data["users"]), name, quota)
    data["users"].append(user)
    return user


def add_folder(data: Catalog, owner_id: int, name: str) -> Folder:
    owner = get_record(data, "users", owner_id)
    name = valid_name(name)
    if any(f.owner is owner and f.name == name for f in data["folders"]):
        raise ValueError("Папка уже существует.")
    folder = Folder(next_id(data["folders"]), name, owner)
    data["folders"].append(folder)
    return folder


def check_access(data: Catalog, user_id: int, folder_id: int,
                 write: bool = False) -> bool:
    user = get_record(data, "users", user_id)
    folder = get_record(data, "folders", folder_id)
    return folder.allows(user, data["accesses"], write)


def set_access(data: Catalog, actor_id: int, folder_id: int,
               user_id: int, level: str) -> None:
    folder = get_record(data, "folders", folder_id)
    user = get_record(data, "users", user_id)
    actor = get_record(data, "users", actor_id)
    if not folder.is_owned_by(actor):
        raise PermissionError("Управлять доступом может только владелец.")
    if user is actor or level not in ("read", "write", "none"):
        raise ValueError("Неверный получатель или уровень доступа.")
    existing = next((a for a in data["accesses"]
                     if a.user is user and a.folder is folder), None)
    if level == "none":
        if existing is not None:
            data["accesses"].remove(existing)
    elif existing is not None:
        existing.change_level(actor, level)
    else:
        data["accesses"].append(Access(user, folder, level))


def used_space(data: Catalog, owner_id: int) -> int:
    owner = get_record(data, "users", owner_id)
    return sum(f.size for f in data["files"] if f.folder.owner is owner)


def add_file(data: Catalog, user_id: int, folder_id: int,
             name: str, size: int) -> File:
    name = valid_name(name)
    nonnegative(size)
    folder = get_record(data, "folders", folder_id)
    if not check_access(data, user_id, folder_id, write=True):
        raise PermissionError("Нет права записи в папку.")
    if not folder.owner.can_store(size, used_space(data, folder.owner.id)):
        raise ValueError("Превышена квота владельца папки.")
    if any(f.folder is folder and f.name == name for f in data["files"]):
        raise ValueError("Файл с таким именем уже существует в папке.")
    record = File(next_id(data["files"]), name, folder, size)
    data["files"].append(record)
    return record


def delete_file(data: Catalog, user_id: int, file_id: int) -> None:
    record = get_record(data, "files", file_id)
    if not check_access(data, user_id, record.folder.id, write=True):
        raise PermissionError("Нет права удаления файла.")
    data["files"].remove(record)


def iter_files(data: Catalog, user_id: int, query: str = "",
               max_size: int | None = None) -> Iterator[File]:
    get_record(data, "users", user_id)
    if max_size is not None:
        nonnegative(max_size)
    for record in data["files"]:
        if not check_access(data, user_id, record.folder.id):
            continue
        if record.matches(query, max_size):
            yield record


def list_files(data: Catalog, user_id: int, query: str = "",
               max_size: int | None = None,
               sort_by: str = "name") -> list[File]:
    if sort_by not in ("name", "size", "uploaded_at"):
        raise ValueError("Сортировка: name, size или uploaded_at.")
    return sorted(iter_files(data, user_id, query, max_size),
                  key=lambda f: (getattr(f, sort_by), f.id))

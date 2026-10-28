"""Операции над пользователями, папками, файлами и правами доступа."""

from collections.abc import Iterator
from datetime import date

from .rules import can_write, has_space

COLLECTIONS = ("users", "folders", "files", "accesses")


def empty_catalog() -> dict:
    """Создать независимые списки сущностей."""
    return {name: [] for name in COLLECTIONS}


def nonnegative(value: int) -> None:
    """Проверить целое неотрицательное количество байт."""
    if type(value) is not int or value < 0:
        raise ValueError("Размер должен быть целым неотрицательным числом.")


def valid_name(name: str) -> str:
    """Нормализовать непустое имя без разделителей пути."""
    if not isinstance(name, str):
        raise ValueError("Имя должно быть строкой.")
    name = name.strip()
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError("Имя пустое или содержит разделители пути.")
    return name


def get_record(data: dict, collection: str, record_id: int) -> dict:
    """Найти запись по ID; неизвестный ID считать ошибкой ввода."""
    for record in data[collection]:
        if record["id"] == record_id:
            return record
    raise ValueError(f"Не найден ID {record_id} в {collection}.")


def next_id(records: list[dict]) -> int:
    """Получить свободный ID, в том числе для пустого списка."""
    return max((record["id"] for record in records), default=0) + 1


def add_user(data: dict, name: str, quota: int) -> dict:
    """Добавить пользователя с уникальным именем и квотой в байтах."""
    name = valid_name(name)
    nonnegative(quota)
    if any(user["name"].casefold() == name.casefold()
           for user in data["users"]):
        raise ValueError("Пользователь с таким именем уже существует.")
    user = {"id": next_id(data["users"]), "name": name, "quota": quota}
    data["users"].append(user)
    return user.copy()


def add_folder(data: dict, owner_id: int, name: str) -> dict:
    """Создать папку владельца; вложенность появится в следующих ПР."""
    get_record(data, "users", owner_id)
    name = valid_name(name)
    if any(f["owner_id"] == owner_id and f["name"] == name
           for f in data["folders"]):
        raise ValueError("Папка уже существует.")
    folder = {"id": next_id(data["folders"]), "owner_id": owner_id,
              "name": name}
    data["folders"].append(folder)
    return folder.copy()


def check_access(data: dict, user_id: int, folder_id: int,
                 write: bool = False) -> bool:
    """Проверить сохранённое право на конкретную папку."""
    user = get_record(data, "users", user_id)
    folder = get_record(data, "folders", folder_id)
    owner = get_record(data, "users", folder["owner_id"])
    access = ""
    for entry in data["accesses"]:
        if entry["user_id"] == user_id and entry["folder_id"] == folder_id:
            access = entry["level"]
            break
    if write:
        return can_write(user["name"], owner["name"], access)
    return user_id == owner["id"] or access in ("read", "write")


def set_access(data: dict, actor_id: int, folder_id: int,
               user_id: int, level: str) -> None:
    """Владелец выдаёт, изменяет или отзывает право (level=none)."""
    folder = get_record(data, "folders", folder_id)
    get_record(data, "users", user_id)
    if actor_id != folder["owner_id"]:
        raise PermissionError("Управлять доступом может только владелец.")
    if user_id == actor_id or level not in ("read", "write", "none"):
        raise ValueError("Неверный получатель или уровень доступа.")
    data["accesses"] = [a for a in data["accesses"]
                        if (a["user_id"], a["folder_id"])
                        != (user_id, folder_id)]
    if level != "none":
        data["accesses"].append({"user_id": user_id, "folder_id": folder_id,
                                 "level": level})


def used_space(data: dict, owner_id: int) -> int:
    """Подсчитать общий размер файлов во всех папках владельца."""
    get_record(data, "users", owner_id)
    folders = {f["id"] for f in data["folders"]
               if f["owner_id"] == owner_id}
    return sum(f["size"] for f in data["files"] if f["folder_id"] in folders)


def add_file(data: dict, user_id: int, folder_id: int,
             name: str, size: int) -> dict:
    """Развить сценарий ПР1: проверить загрузку и сохранить запись файла."""
    name = valid_name(name)
    nonnegative(size)
    folder = get_record(data, "folders", folder_id)
    if not check_access(data, user_id, folder_id, write=True):
        raise PermissionError("Нет права записи в папку.")
    owner = get_record(data, "users", folder["owner_id"])
    if not has_space(size, used_space(data, owner["id"]), owner["quota"]):
        raise ValueError("Превышена квота владельца папки.")
    if any(f["folder_id"] == folder_id and f["name"] == name
           for f in data["files"]):
        raise ValueError("Файл с таким именем уже существует в папке.")
    record = {"id": next_id(data["files"]), "folder_id": folder_id,
              "name": name, "size": size,
              "uploaded_at": date.today().isoformat()}
    data["files"].append(record)
    return record.copy()


def delete_file(data: dict, user_id: int, file_id: int) -> None:
    """Удалить запись файла и тем самым освободить квоту."""
    record = get_record(data, "files", file_id)
    if not check_access(data, user_id, record["folder_id"], write=True):
        raise PermissionError("Нет права удаления файла.")
    data["files"].remove(record)


def iter_files(data: dict, user_id: int, query: str = "",
               max_size: int | None = None) -> Iterator[dict]:
    """Перебирать доступные файлы с поиском по имени и отбором по размеру."""
    get_record(data, "users", user_id)
    if max_size is not None:
        nonnegative(max_size)
    for record in data["files"]:
        if not check_access(data, user_id, record["folder_id"]):
            continue
        if query.casefold() not in record["name"].casefold():
            continue
        if max_size is None or record["size"] <= max_size:
            yield record.copy()


def list_files(data: dict, user_id: int, query: str = "",
               max_size: int | None = None,
               sort_by: str = "name") -> list[dict]:
    """Вывести результат поиска в порядке имени, размера или даты."""
    if sort_by not in ("name", "size", "uploaded_at"):
        raise ValueError("Сортировка: name, size или uploaded_at.")
    return sorted(iter_files(data, user_id, query, max_size),
                  key=lambda f: (f[sort_by], f["id"]))

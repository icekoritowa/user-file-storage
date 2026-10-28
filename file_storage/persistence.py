import json
import os
import tempfile
from datetime import date
from pathlib import Path

from .catalog import COLLECTIONS, Catalog, empty_catalog
from .models import Access, File, Folder, User
from .validation import nonnegative, valid_name


def validate_payload(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != set(COLLECTIONS):
        raise ValueError("Ожидаются users, folders, files, accesses.")
    for name in COLLECTIONS:
        if not isinstance(data[name], list):
            raise ValueError(f"{name} должен быть списком.")
        if any(not isinstance(row, dict) for row in data[name]):
            raise ValueError(f"Записи {name} должны быть словарями.")
    try:
        for name in COLLECTIONS[:3]:
            ids = set()
            for row in data[name]:
                if type(row["id"]) is not int or row["id"] <= 0:
                    raise ValueError("ID должен быть положительным целым.")
                if row["id"] in ids or valid_name(row["name"]) != row["name"]:
                    raise ValueError("Повтор ID или некорректное имя.")
                ids.add(row["id"])
        users = {u["id"]: u for u in data["users"]}
        folders = {f["id"]: f for f in data["folders"]}
        names = [u["name"].casefold() for u in users.values()]
        if len(names) != len(set(names)):
            raise ValueError("Повтор имени пользователя.")
        for user in users.values():
            nonnegative(user["quota"])
        folder_names = set()
        for folder in folders.values():
            owner = folder["owner_id"]
            if type(owner) is not int or owner not in users:
                raise ValueError("Неизвестный владелец папки.")
            key = (owner, folder["name"])
            if key in folder_names:
                raise ValueError("Повтор имени папки.")
            folder_names.add(key)
        used = {uid: 0 for uid in users}
        file_names = set()
        for record in data["files"]:
            fid = record["folder_id"]
            if type(fid) is not int or fid not in folders:
                raise ValueError("Неизвестная папка файла.")
            nonnegative(record["size"])
            date.fromisoformat(record["uploaded_at"])
            used[folders[fid]["owner_id"]] += record["size"]
            key = (fid, record["name"])
            if key in file_names:
                raise ValueError("Повтор имени файла.")
            file_names.add(key)
        if any(used[uid] > users[uid]["quota"] for uid in users):
            raise ValueError("Превышена квота в сохранённых данных.")
        access_keys = set()
        for entry in data["accesses"]:
            uid, fid = entry["user_id"], entry["folder_id"]
            if (type(uid) is not int or type(fid) is not int
                    or uid not in users or fid not in folders):
                raise ValueError("Неизвестный пользователь или папка доступа.")
            if (entry["level"] not in ("read", "write")
                    or uid == folders[fid]["owner_id"]
                    or (uid, fid) in access_keys):
                raise ValueError("Некорректное или повторное право доступа.")
            access_keys.add((uid, fid))
    except (KeyError, TypeError) as error:
        raise ValueError("Неверные поля JSON.") from error


def from_data(payload: dict) -> Catalog:
    validate_payload(payload)
    users = {row["id"]: User.from_dict(row) for row in payload["users"]}
    folders = {row["id"]: Folder.from_dict(row, users)
               for row in payload["folders"]}
    return {"users": list(users.values()), "folders": list(folders.values()),
            "files": [File.from_dict(row, folders)
                      for row in payload["files"]],
            "accesses": [Access.from_dict(row, users, folders)
                         for row in payload["accesses"]]}


def to_data(data: Catalog) -> dict:
    if not isinstance(data, dict) or set(data) != set(COLLECTIONS):
        raise ValueError("Неверная структура каталога.")
    types = (User, Folder, File, Access)
    for name, entity_type in zip(COLLECTIONS, types):
        if not isinstance(data[name], list) or any(
            not isinstance(item, entity_type) for item in data[name]
        ):
            raise ValueError(f"Неверные объекты в {name}.")
    users = {u.id: u for u in data["users"]}
    folders = {f.id: f for f in data["folders"]}
    for folder in data["folders"]:
        if users.get(folder.owner.id) is not folder.owner:
            raise ValueError("Папка ссылается на посторонний объект User.")
    for record in data["files"]:
        if folders.get(record.folder.id) is not record.folder:
            raise ValueError("Файл ссылается на посторонний объект Folder.")
    for access in data["accesses"]:
        if (users.get(access.user.id) is not access.user
                or folders.get(access.folder.id) is not access.folder):
            raise ValueError("Доступ ссылается на посторонние объекты.")
    payload = {name: [record.to_dict() for record in data[name]]
               for name in COLLECTIONS}
    validate_payload(payload)
    return payload


def load_catalog(path: Path) -> Catalog:
    try:
        with path.open(encoding="utf-8") as stream:
            payload = json.load(stream)
    except FileNotFoundError:
        return empty_catalog()
    return from_data(payload)


def save_catalog(path: Path, data: Catalog) -> None:
    payload = to_data(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

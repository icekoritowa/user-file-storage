from __future__ import annotations

from datetime import date

from .rules import has_space
from .validation import nonnegative, positive_id, valid_name


class NamedEntity:
    def __init__(self, entity_id: int, name: str) -> None:
        positive_id(entity_id)
        self._id = entity_id
        self._name = valid_name(name)

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return f"{type(self).__name__} #{self.id}: {self.name}"


class User(NamedEntity):
    def __init__(self, user_id: int, name: str, quota: int) -> None:
        super().__init__(user_id, name)
        nonnegative(quota)
        self._quota = quota

    @property
    def quota(self) -> int:
        return self._quota

    def can_store(self, size: int, used: int) -> bool:
        nonnegative(size)
        nonnegative(used)
        return has_space(size, used, self.quota)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "quota": self.quota}

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(data["id"], data["name"], data["quota"])

    def __str__(self) -> str:
        return f"Пользователь #{self.id}: {self.name}, квота {self.quota} байт"


class Folder(NamedEntity):
    def __init__(self, folder_id: int, name: str, owner: User) -> None:
        super().__init__(folder_id, name)
        if not isinstance(owner, User):
            raise ValueError("Владелец должен быть объектом User.")
        self._owner = owner

    @property
    def owner(self) -> User:
        return self._owner

    def is_owned_by(self, user: User) -> bool:
        return self.owner is user

    def allows(self, user: User, accesses: list[Access],
               write: bool = False) -> bool:
        if self.is_owned_by(user):
            return True
        return any(access.user is user and access.folder is self
                   and access.allows(write) for access in accesses)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "owner_id": self.owner.id}

    @classmethod
    def from_dict(cls, data: dict, users: dict[int, User]) -> Folder:
        return cls(data["id"], data["name"], users[data["owner_id"]])

    def __str__(self) -> str:
        return f"Папка #{self.id}: {self.name}, владелец {self.owner.name}"


class File(NamedEntity):
    def __init__(self, file_id: int, name: str, folder: Folder,
                 size: int, uploaded_at: date | None = None) -> None:
        super().__init__(file_id, name)
        if not isinstance(folder, Folder):
            raise ValueError("Папка должна быть объектом Folder.")
        nonnegative(size)
        if uploaded_at is not None and type(uploaded_at) is not date:
            raise ValueError("Дата должна быть объектом date.")
        self._folder = folder
        self._size = size
        self._uploaded_at = uploaded_at or date.today()

    @property
    def folder(self) -> Folder:
        return self._folder

    @property
    def size(self) -> int:
        return self._size

    @property
    def uploaded_at(self) -> date:
        return self._uploaded_at

    def matches(self, query: str, max_size: int | None = None) -> bool:
        if max_size is not None:
            nonnegative(max_size)
        return (query.casefold() in self.name.casefold()
                and (max_size is None or self.size <= max_size))

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "folder_id": self.folder.id,
                "size": self.size, "uploaded_at": self.uploaded_at.isoformat()}

    @classmethod
    def from_dict(cls, data: dict, folders: dict[int, Folder]) -> File:
        return cls(data["id"], data["name"], folders[data["folder_id"]],
                   data["size"], date.fromisoformat(data["uploaded_at"]))

    def __str__(self) -> str:
        return (f"Файл #{self.id}: {self.folder.name}/{self.name}, "
                f"{self.size} байт, {self.uploaded_at.isoformat()}")


class Access:
    LEVELS = ("read", "write")

    def __init__(self, user: User, folder: Folder, level: str) -> None:
        if not isinstance(user, User) or not isinstance(folder, Folder):
            raise ValueError("Ожидаются User и Folder.")
        if folder.is_owned_by(user):
            raise ValueError("Владелец уже имеет полный доступ.")
        self.validate_level(level)
        self._user = user
        self._folder = folder
        self._level = level

    @property
    def user(self) -> User:
        return self._user

    @property
    def folder(self) -> Folder:
        return self._folder

    @property
    def level(self) -> str:
        return self._level

    @staticmethod
    def validate_level(level: str) -> None:
        if level not in Access.LEVELS:
            raise ValueError("Уровень доступа должен быть read или write.")

    def change_level(self, actor: User, level: str) -> None:
        if not self.folder.is_owned_by(actor):
            raise PermissionError("Управлять доступом может только владелец.")
        self.validate_level(level)
        self._level = level

    def allows(self, write: bool = False) -> bool:
        return not write or self.level == "write"

    def to_dict(self) -> dict:
        return {"user_id": self.user.id, "folder_id": self.folder.id,
                "level": self.level}

    @classmethod
    def from_dict(cls, data: dict, users: dict[int, User],
                  folders: dict[int, Folder]) -> Access:
        return cls(users[data["user_id"]], folders[data["folder_id"]],
                   data["level"])

    def __str__(self) -> str:
        return f"Доступ: {self.user.name} → {self.folder.name}: {self.level}"

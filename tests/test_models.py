from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from file_storage import catalog as c
from file_storage.models import Access, File, Folder, NamedEntity, User
from file_storage.persistence import (
    from_data, load_catalog, save_catalog, to_data,
)


def test_constructors_methods_and_polymorphism():
    user = User(1, "ilya", 100)
    guest = User(2, "guest", 50)
    folder = Folder(1, "Учеба", user)
    file = File(1, "a.pdf", folder, 10, date(2026, 10, 28))
    access = Access(guest, folder, "read")
    assert folder.owner is user
    assert file.folder is folder
    assert access.user is guest and access.folder is folder
    assert user.can_store(20, 80)
    assert not user.can_store(21, 80)
    assert file.matches("PDF", 10)
    assert not file.matches("PDF", 9)
    assert folder.allows(user, [])
    assert folder.allows(guest, [access])
    assert not folder.allows(guest, [access], write=True)
    access.change_level(user, "write")
    assert folder.allows(guest, [access], write=True)
    assert Access.LEVELS == ("read", "write")
    assert all(isinstance(entity, NamedEntity)
               for entity in (user, folder, file))
    labels = [str(entity) for entity in (user, folder, file, access)]
    assert labels[0].startswith("Пользователь #1")
    assert labels[1].startswith("Папка #1")
    assert "Учеба/a.pdf" in labels[2]
    assert "guest" in labels[3] and "write" in labels[3]


@pytest.mark.parametrize("field,value", [
    ("id", 2), ("name", "changed"), ("quota", -1),
])
def test_user_public_attributes_are_readonly(field, value):
    user = User(1, "ilya", 100)
    with pytest.raises(AttributeError):
        setattr(user, field, value)
    assert user.to_dict() == {"id": 1, "name": "ilya", "quota": 100}


@pytest.mark.parametrize("factory", [
    lambda: User(True, "a", 10),
    lambda: User(0, "a", 10),
    lambda: User(1, " ", 10),
    lambda: User(1, "a", -1),
    lambda: Folder(1, "f", 1),
    lambda: File(1, "a", Folder(1, "f", User(1, "u", 10)), -1),
    lambda: File(1, "a", Folder(1, "f", User(1, "u", 10)), 0, "bad"),
])
def test_invalid_objects(factory):
    with pytest.raises(ValueError):
        factory()


def test_access_change_preserves_state_on_error():
    owner, guest = User(1, "a", 10), User(2, "b", 10)
    folder = Folder(1, "f", owner)
    access = Access(guest, folder, "read")
    with pytest.raises(PermissionError):
        access.change_level(guest, "write")
    with pytest.raises(ValueError):
        access.change_level(owner, "unknown")
    with pytest.raises(AttributeError):
        access.level = "write"
    with pytest.raises(ValueError):
        Access(owner, folder, "read")
    assert access.level == "read"


def test_pr2_json_migration_and_reference_identity(tmp_path):
    example = Path(__file__).resolve().parents[1] / "data/example.json"
    data = load_catalog(example)
    assert isinstance(data["users"][0], User)
    assert isinstance(data["folders"][0], Folder)
    assert isinstance(data["files"][0], File)
    assert isinstance(data["accesses"][0], Access)
    assert data["folders"][0].owner is data["users"][0]
    assert data["files"][0].folder is data["folders"][0]
    assert data["accesses"][0].folder is data["folders"][0]
    assert data["accesses"][0].user is data["users"][1]
    target = tmp_path / "roundtrip.json"
    save_catalog(target, data)
    restored = load_catalog(target)
    assert to_data(restored) == to_data(data)
    assert restored["files"][0].folder.owner is restored["users"][0]
    clone = deepcopy(data)
    assert clone["files"][0].folder is clone["folders"][0]
    assert clone["folders"][0].owner is not data["users"][0]


def test_detached_object_rejected_on_save(tmp_path):
    data = c.empty_catalog()
    c.add_user(data, "ilya", 100)
    detached_user = User(1, "ilya", 100)
    data["folders"].append(Folder(1, "f", detached_user))
    with pytest.raises(ValueError, match="посторонний"):
        save_catalog(tmp_path / "invalid.json", data)
    assert not (tmp_path / "invalid.json").exists()


def test_classmethod_and_independent_instances():
    user = User.from_dict({"id": 1, "name": "a", "quota": 100})
    other = User(2, "b", 50)
    assert user.id != other.id and user.quota != other.quota
    data = c.empty_catalog()
    data["users"] = [user, other]
    folder = c.add_folder(data, user.id, "f")
    c.set_access(data, user.id, folder.id, other.id, "read")
    access = data["accesses"][0]
    c.set_access(data, user.id, folder.id, other.id, "write")
    assert data["accesses"][0] is access
    assert access.level == "write"
    assert from_data(to_data(data))["accesses"][0].level == "write"

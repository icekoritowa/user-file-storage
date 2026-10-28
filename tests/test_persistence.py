import json
from copy import deepcopy

import pytest

from file_storage import catalog as c
from file_storage import persistence as p


def sample():
    data = c.empty_catalog()
    c.add_user(data, "Илья", 100)
    c.add_folder(data, 1, "Учеба")
    c.add_file(data, 1, 1, "ПР2.txt", 50)
    return data


def test_roundtrip_and_missing(tmp_path):
    path = tmp_path / "sub" / "catalog.json"
    assert p.load_catalog(path) == c.empty_catalog()
    data = sample()
    p.save_catalog(path, data)
    assert p.to_data(p.load_catalog(path)) == p.to_data(data)
    assert "Илья" in path.read_text()
    c.delete_file(data, 1, 1)
    p.save_catalog(path, data)
    assert p.load_catalog(path)["files"] == []


@pytest.mark.parametrize("text", ["{broken", "[]", "{}", '{"users": null}'])
def test_invalid_json_is_not_replaced(tmp_path, text):
    path = tmp_path / "catalog.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        p.load_catalog(path)
    assert path.read_text() == text


@pytest.mark.parametrize("change", [
    lambda d: d["files"][0].update(folder_id=999),
    lambda d: d["files"][0].update(size=-1),
    lambda d: d["files"][0].update(size=101),
    lambda d: d["files"][0].update(uploaded_at="bad-date"),
    lambda d: d["users"][0].update(id=True),
    lambda d: d["users"].append(d["users"][0].copy()),
    lambda d: d["accesses"].append({"user_id": 99, "folder_id": 1,
                                    "level": "read"}),
    lambda d: d["folders"][0].pop("owner_id"),
])
def test_schema_validation(tmp_path, change):
    data = p.to_data(sample())
    change(data)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        p.load_catalog(path)


def test_write_failure_keeps_old_file(tmp_path, monkeypatch):
    path = tmp_path / "catalog.json"
    original = sample()
    p.save_catalog(path, original)
    changed = deepcopy(original)
    c.add_file(changed, 1, 1, "new", 1)

    def fail(*args):
        raise OSError("Диск недоступен")

    monkeypatch.setattr(p.os, "replace", fail)
    with pytest.raises(OSError):
        p.save_catalog(path, changed)
    assert p.to_data(p.load_catalog(path)) == p.to_data(original)
    assert len(list(tmp_path.iterdir())) == 1

import pytest

from file_storage import catalog as c
from file_storage.persistence import to_data


@pytest.fixture
def data():
    data = c.empty_catalog()
    c.add_user(data, "ilya", 100)
    c.add_user(data, "guest", 50)
    c.add_folder(data, 1, "Учеба")
    c.add_folder(data, 1, "Личное")
    c.add_folder(data, 2, "Гостевое")
    return data


def test_upload_exact_quota_and_delete(data):
    c.add_file(data, 1, 1, "a.txt", 80)
    last = c.add_file(data, 1, 2, "b.txt", 20)
    assert c.used_space(data, 1) == 100
    with pytest.raises(ValueError, match="квота"):
        c.add_file(data, 1, 1, "c", 1)
    c.delete_file(data, 1, last.id)
    assert c.used_space(data, 1) == 80


def test_access_lifecycle_and_owner_quota(data):
    c.add_file(data, 1, 1, "a", 80)
    assert c.list_files(data, 2) == []
    c.set_access(data, 1, 1, 2, "read")
    assert len(c.list_files(data, 2)) == 1
    with pytest.raises(PermissionError):
        c.add_file(data, 2, 1, "b", 1)
    with pytest.raises(PermissionError):
        c.delete_file(data, 2, 1)
    c.set_access(data, 1, 1, 2, "write")
    c.add_file(data, 2, 1, "b", 20)
    assert c.used_space(data, 1) == 100
    assert c.used_space(data, 2) == 0
    c.set_access(data, 1, 1, 2, "none")
    assert not c.check_access(data, 2, 1)
    assert c.list_files(data, 2) == []


def test_guest_cannot_grant_access(data):
    c.set_access(data, 1, 1, 2, "write")
    before = to_data(data)
    with pytest.raises(PermissionError):
        c.set_access(data, 2, 1, 1, "write")
    assert to_data(data) == before


def test_find_filter_sort_and_generator(data):
    c.add_file(data, 1, 1, "z.PDF", 20)
    c.add_file(data, 1, 2, "a.pdf", 10)
    c.add_file(data, 1, 2, "b.txt", 0)
    result = c.list_files(data, 1, ".pdf", sort_by="size")
    assert [f.name for f in result] == ["a.pdf", "z.PDF"]
    assert [f.name for f in c.iter_files(data, 1, max_size=0)] == ["b.txt"]
    assert result[0] is data["files"][1]
    with pytest.raises(AttributeError):
        result[0].name = "changed"
    assert data["files"][1].name == "a.pdf"
    with pytest.raises(ValueError):
        c.list_files(data, 1, sort_by="unknown")


@pytest.mark.parametrize("size", [-1, 1.2, True, "1"])
def test_invalid_size_does_not_mutate(data, size):
    before = to_data(data)
    with pytest.raises(ValueError):
        c.add_file(data, 1, 1, "a", size)
    assert to_data(data) == before


@pytest.mark.parametrize("name", ["", " ", "../a", "a/b", "a\\b"])
def test_invalid_names(data, name):
    with pytest.raises(ValueError):
        c.add_folder(data, 1, name)


def test_duplicates_and_missing_ids(data):
    with pytest.raises(ValueError):
        c.add_user(data, "ILYA", 10)
    with pytest.raises(ValueError):
        c.add_folder(data, 1, "Учеба")
    c.add_file(data, 1, 1, "a", 0)
    with pytest.raises(ValueError):
        c.add_file(data, 1, 1, "a", 0)
    with pytest.raises(ValueError):
        c.add_file(data, 1, 999, "a", 0)
    with pytest.raises(ValueError):
        c.delete_file(data, 1, 999)
    with pytest.raises(ValueError):
        c.list_files(data, 999)

import subprocess
import sys
from pathlib import Path

import pytest

from file_storage.rules import MIB, can_write, has_space, upload_file


@pytest.mark.parametrize("user,owner,access,expected", [
    ("ilya", "ilya", "read", True),
    ("guest", "ilya", "write", True),
    ("guest", "ilya", "read", False),
    ("guest", "ilya", "unknown", False),
    ("", "ilya", "write", False),
    ("guest", " ", "write", False),
])
def test_access(user, owner, access, expected):
    assert can_write(user, owner, access) is expected


@pytest.mark.parametrize("size,used,quota,expected", [
    (10, 80, 100, True),
    (20, 80, 100, True),
    (21, 80, 100, False),
    (0, 100, 100, True),
    (0, 0, 0, True),
    (-1, 80, 100, False),
    (1, -1, 100, False),
    (1, 0, -1, False),
    (0, 101, 100, False),
])
def test_quota(size, used, quota, expected):
    assert has_space(size, used, quota) is expected


def test_success():
    result = upload_file("ilya", "ilya", "read", "Учеба", "a.pdf",
                         12 * MIB, 80 * MIB, 100 * MIB)
    assert "Учеба/a.pdf" in result
    assert "8.00 МиБ" in result


def test_guest_with_write_access():
    result = upload_file("guest", "ilya", "write", "Учеба", "a.pdf",
                         20, 80, 100)
    assert result.startswith("Загрузка разрешена")


@pytest.mark.parametrize("folder,name", [("", "a"), ("a", " ")])
def test_empty_names(folder, name):
    result = upload_file("ilya", "ilya", "write", folder, name, 1, 0, 10)
    assert "не должны быть пустыми" in result


def test_access_denied():
    result = upload_file("guest", "ilya", "read", "Учеба", "a.pdf",
                         1, 0, 100)
    assert "нет права записи" in result


def test_quota_denied():
    result = upload_file("ilya", "ilya", "write", "Учеба", "a.pdf",
                         21, 80, 100)
    assert "превышена квота" in result


def test_demo_runs():
    project = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(project / "main.py"), "--demo"],
        capture_output=True, text=True, check=True,
    )
    assert "7.50 МиБ" in result.stdout
    assert result.stdout.count("Отказ:") == 2

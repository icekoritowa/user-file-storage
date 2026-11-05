import sqlite3
from contextlib import contextmanager
from pathlib import Path

from file_storage.persistence import from_data

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "storage.sqlite"


@contextmanager
def connect(path=DEFAULT_PATH, readonly=False):
    path = Path(path)
    target = path.resolve().as_uri() + "?mode=ro" if readonly else str(path)
    connection = sqlite3.connect(target, uri=readonly)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def load_database(path):
    with connect(path, readonly=True) as connection:
        data = {
            "users": [dict(r) for r in connection.execute(
                "SELECT id, name, quota FROM users")],
            "folders": [dict(r) for r in connection.execute(
                "SELECT id, name, owner_id FROM folders")],
            "files": [dict(r) for r in connection.execute(
                "SELECT id, name, folder_id, size, uploaded_at FROM files")],
            "accesses": [dict(r) for r in connection.execute(
                "SELECT user_id, folder_id, level FROM accesses")],
        }
    return from_data(data)

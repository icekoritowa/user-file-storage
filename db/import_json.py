import argparse
from pathlib import Path

from db.database import DEFAULT_PATH, ROOT, connect
from file_storage.persistence import load_catalog, to_data


def import_json(source, target=DEFAULT_PATH):
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    data = to_data(load_catalog(source))
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    with connect(target) as connection:
        connection.executescript((ROOT / "sql/schema.sql").read_text())
        with connection:
            for table in ("accesses", "files", "folders", "users"):
                connection.execute("DELETE FROM " + table)
            for table, rows in data.items():
                if rows:
                    columns = list(rows[0])
                    placeholders = ",".join("?" for _ in columns)
                    statement = ("INSERT INTO " + table + " ("
                                 + ",".join(columns) + ") VALUES ("
                                 + placeholders + ")")
                    connection.executemany(statement, [
                        tuple(row[c] for c in columns) for row in rows
                    ])
    return {name: len(rows) for name, rows in data.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--database", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    print(import_json(args.source, args.database))

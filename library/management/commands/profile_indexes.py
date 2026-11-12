import json
import sqlite3
from statistics import median
from time import perf_counter

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from library.models import File


def measure(database, sql, params):
    plan = [row[3] for row in database.execute(
        "EXPLAIN QUERY PLAN " + sql, params,
    )]
    timings = []
    rows = []
    for _ in range(25):
        start = perf_counter()
        rows = database.execute(sql, params).fetchall()
        timings.append((perf_counter() - start) * 1000)
    return {"plan": plan, "median_ms": round(median(timings), 4)}, rows


class Command(BaseCommand):
    def handle(self, *args, **options):
        if connection.vendor != "sqlite":
            raise CommandError("Профилирование рассчитано на SQLite.")
        connection.ensure_connection()
        database = sqlite3.connect(":memory:")
        try:
            connection.connection.backup(database)
            database.execute("PRAGMA foreign_keys = ON")
            for table in ("permissions_access", "library_file",
                          "library_folder", "library_user"):
                database.execute("DELETE FROM " + table)
            database.execute(
                "INSERT INTO library_user (id,name,quota) VALUES (1,?,?)",
                ("benchmark", 10**12),
            )
            database.executemany(
                "INSERT INTO library_folder (id,name,owner_id) VALUES (?,?,1)",
                [(i, f"folder-{i}") for i in range(1, 21)],
            )
            database.executemany(
                "INSERT INTO library_file "
                "(id,name,folder_id,size,uploaded_at) VALUES (?,?,?,?,?)",
                [(i, f"file-{i}", i % 20 + 1, i * 137 % 1000000,
                  f"2026-10-{i % 28 + 1:02d}") for i in range(1, 50001)],
            )
            queries = [
                ("folder_date", "file_folder_date_idx",
                 "folder_id, uploaded_at DESC, id",
                 File.objects.filter(folder_id=1).order_by(
                     "-uploaded_at", "id").values("id", "name")[:10]),
                ("size", "file_size_id_idx", "size DESC, id",
                 File.objects.filter(size__lte=500000).order_by(
                     "-size", "id").values("id", "name")[:10]),
            ]
            results = {"rows": 50000, "repeats": 25,
                       "sqlite": sqlite3.sqlite_version, "queries": {}}
            for label, index, fields, queryset in queries:
                sql, params = queryset.query.sql_with_params()
                sql = sql.replace("%s", "?")
                database.execute("DROP INDEX IF EXISTS " + index)
                before, old_rows = measure(database, sql, params)
                database.execute("CREATE INDEX " + index
                                 + " ON library_file (" + fields + ")")
                after, new_rows = measure(database, sql, params)
                if old_rows != new_rows:
                    raise CommandError("Результаты запросов различаются.")
                results["queries"][label] = {
                    "before": before, "after": after, "same_results": True,
                }
            self.stdout.write(json.dumps(
                results, ensure_ascii=False, indent=2,
            ))
        finally:
            database.close()

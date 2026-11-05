import sqlite3
from datetime import date

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_safe

from db.database import ROOT, connect

SECTIONS = [
    ('Пользователи', ()),
    ('Папки', ()),
    ('Поиск файлов', ('pattern', 'size', 'date', 'offset')),
    ('Права записи', ()),
    ('Файлы и владельцы', ()),
    ('Выданный доступ', ()),
    ('Объём файлов', ()),
    ('Квоты', ()),
    ('Файлы по папкам', ('minimum',)),
    ('Папки со свободным местом', ('size',)),
    ('Файлы по датам', ()),
    ('Пользователи без email', ()),
]


@require_safe
def statistics(request):
    try:
        values = {
            "pattern": "%" + request.GET.get("q", "") + "%",
            "size": int(request.GET.get("size", "104857600")),
            "date": date.fromisoformat(request.GET.get(
                "date", date.today().isoformat())).isoformat(),
            "offset": int(request.GET.get("offset", "0")),
            "minimum": int(request.GET.get("minimum", "0")),
        }
        if any(values[k] < 0 for k in ("size", "offset", "minimum")):
            raise ValueError
    except ValueError:
        return render(request, "db/statistics.html", {
            "error": "Введите дату и неотрицательные целые числа.",
        }, status=400)
    queries = (ROOT / "sql/queries.sql").read_text().split(";")
    sections = []
    try:
        with connect(settings.STORAGE_DATABASE, readonly=True) as connection:
            for (title, keys), query in zip(SECTIONS, queries):
                cursor = connection.execute(query, [values[k] for k in keys])
                sections.append({
                    "title": title,
                    "columns": [c[0] for c in cursor.description],
                    "rows": [list(row) for row in cursor.fetchall()],
                })
    except sqlite3.Error:
        return render(request, "503.html", status=503)
    return render(request, "db/statistics.html", {
        "sections": sections, "values": values,
        "q": request.GET.get("q", ""),
    })

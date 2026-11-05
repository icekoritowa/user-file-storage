import sqlite3
from functools import wraps

from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_safe

from file_storage.persistence import load_catalog
from db.database import load_database


def catalog_view(view):
    @wraps(view)
    @require_safe
    def wrapped(request, *args, **kwargs):
        try:
            path = settings.CATALOG_PATH
            if not path.exists():
                path = settings.EXAMPLE_PATH
            data = (load_database(settings.STORAGE_DATABASE)
                    if settings.STORAGE_DATABASE else load_catalog(path))
        except (OSError, ValueError, sqlite3.Error):
            return render(request, "503.html", status=503)
        return view(request, data, *args, **kwargs)
    return wrapped

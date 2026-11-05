from functools import wraps

from django.db import DatabaseError
from django.shortcuts import render
from django.views.decorators.http import require_safe


def database_view(view):
    @wraps(view)
    @require_safe
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except DatabaseError:
            return render(request, "503.html", status=503)
    return wrapped

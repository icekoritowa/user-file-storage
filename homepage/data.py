from functools import wraps

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_safe

from file_storage.persistence import load_catalog
from .layout import page


def catalog_view(view):
    @wraps(view)
    @require_safe
    def wrapped(request, *args, **kwargs):
        try:
            path = settings.CATALOG_PATH
            if not path.exists():
                path = settings.EXAMPLE_PATH
            data = load_catalog(path)
        except (OSError, ValueError):
            return HttpResponse(page("Ошибка чтения", (
                '<h1>Каталог временно недоступен</h1>'
                '<p>Не удалось прочитать данные. Проверьте JSON-файл.</p>'
            )), status=503)
        return view(request, data, *args, **kwargs)
    return wrapped

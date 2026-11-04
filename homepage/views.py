from django.http import HttpRequest, HttpResponse

from .data import catalog_view
from .layout import link, page


@catalog_view
def index(request: HttpRequest, data: dict) -> HttpResponse:
    content = (
        '<h1 class="display-5">Система хранения пользовательских файлов</h1>'
        '<p class="lead">Папки, файлы и права доступа в одном каталоге.</p>'
        '<p>Хранятся сведения о файлах: имя, размер, дата и владелец.</p>'
        f'<p>Пользователей: {len(data["users"])}. '
        f'Папок: {len(data["folders"])}. Файлов: {len(data["files"])}.</p>'
        '<ul><li>' + link("library:folders", "Открыть папки") + '</li><li>'
        + link("library:files", "Открыть файлы") + '</li><li>'
        + link("permissions:accesses", "Посмотреть права доступа")
        + '</li></ul>'
    )
    return HttpResponse(page("Главная", content))


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    content = ('<h1 class="text-danger">404 — страница не найдена</h1>'
               '<p>Такого адреса или объекта нет в каталоге.</p>'
               + link("homepage:index", "Вернуться на главную"))
    return HttpResponse(page("Страница не найдена", content), status=404)

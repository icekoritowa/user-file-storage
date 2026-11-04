from html import escape

from django.http import Http404, HttpRequest, HttpResponse

from file_storage.catalog import get_record, used_space
from homepage.data import catalog_view
from homepage.layout import link, page


def find(data: dict, collection: str, identifier: int):
    try:
        return get_record(data, collection, identifier)
    except ValueError as error:
        raise Http404("Объект не найден") from error


def file_list(records: list) -> str:
    rows = "".join(
        '<tr><td>' + link("library:file_detail", item.name, item.id)
        + f'</td><td>{item.size}</td><td>{item.uploaded_at}</td></tr>'
        for item in records
    )
    if not rows:
        return '<p class="text-muted">Файлов пока нет.</p>'
    return ('<table class="table table-striped"><thead><tr><th>Файл</th>'
            '<th>Размер, байт</th><th>Дата</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


@catalog_view
def folders(request: HttpRequest, data: dict) -> HttpResponse:
    rows = "".join(
        '<li class="list-group-item">'
        + link("library:folder_detail", folder.name, folder.id)
        + f' — владелец: {escape(folder.owner.name)}</li>'
        for folder in data["folders"]
    )
    content = '<h1>Папки</h1>'
    content += (f'<ul class="list-group">{rows}</ul>' if rows
                else '<p>Папок пока нет.</p>')
    return HttpResponse(page("Папки", content))


@catalog_view
def folder_detail(request: HttpRequest, data: dict,
                  folder_id: int) -> HttpResponse:
    folder = find(data, "folders", folder_id)
    used = used_space(data, folder.owner.id)
    content = (
        f'<h1>{escape(folder.name)}</h1>'
        f'<p>Владелец: {escape(folder.owner.name)}</p>'
        f'<p>Во всех папках владельца занято {used} '
        f'из {folder.owner.quota} байт. '
        f'Свободно: {folder.owner.quota - used} байт.</p>'
        '<h2>Файлы папки</h2>'
        + file_list([f for f in data["files"] if f.folder is folder])
        + link("library:folders", "Назад к папкам")
    )
    return HttpResponse(page(folder.name, content))


@catalog_view
def files(request: HttpRequest, data: dict) -> HttpResponse:
    return HttpResponse(page("Файлы", '<h1>Файлы</h1>'
                             + file_list(data["files"])))


@catalog_view
def file_detail(request: HttpRequest, data: dict,
                file_id: int) -> HttpResponse:
    item = find(data, "files", file_id)
    content = (
        f'<h1>{escape(item.name)}</h1><dl class="row">'
        f'<dt>Размер</dt><dd>{item.size} байт</dd>'
        f'<dt>Дата загрузки</dt><dd>{item.uploaded_at}</dd>'
        f'<dt>Владелец</dt><dd>{escape(item.folder.owner.name)}</dd>'
        '<dt>Папка</dt><dd>'
        + link("library:folder_detail", item.folder.name, item.folder.id)
        + '</dd></dl>' + link("library:files", "Назад к файлам")
    )
    return HttpResponse(page(item.name, content))

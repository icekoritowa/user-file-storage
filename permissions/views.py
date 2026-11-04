from html import escape

from django.http import HttpRequest, HttpResponse

from homepage.data import catalog_view
from homepage.layout import link, page


@catalog_view
def accesses(request: HttpRequest, data: dict) -> HttpResponse:
    rows = "".join(
        f'<tr><td>{escape(access.user.name)}</td><td>'
        + link("library:folder_detail", access.folder.name, access.folder.id)
        + f'</td><td>{escape(access.level)}</td></tr>'
        for access in data["accesses"]
    )
    content = ('<h1>Права доступа</h1><p>read — чтение; '
               'write — чтение, добавление и удаление. '
               'Владелец всегда имеет полный доступ к своей папке.</p>')
    content += (
        '<table class="table table-striped"><thead><tr><th>Пользователь</th>'
        '<th>Папка</th><th>Право</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>' if rows
        else '<p>Дополнительные права пока не выданы.</p>'
    )
    return HttpResponse(page("Права доступа", content))

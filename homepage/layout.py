from html import escape

from django.urls import reverse

BOOTSTRAP = ("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/"
             "dist/css/bootstrap.min.css")


def link(route: str, label: str, *args: int) -> str:
    return f'<a href="{reverse(route, args=args)}">{escape(label)}</a>'


def page(title: str, content: str) -> str:
    navigation = " · ".join([
        link("homepage:index", "Главная"),
        link("library:folders", "Папки"),
        link("library:files", "Файлы"),
        link("permissions:accesses", "Доступ"),
    ])
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — Файловое хранилище</title>
<link href="{BOOTSTRAP}" rel="stylesheet">
<style>
body {{background:#f3f5f7;color:#182530;font-family:system-ui,sans-serif;}}
main {{max-width:1050px;margin:2rem auto;padding:1.5rem;background:white;}}
nav {{padding:1rem;background:#e3eaf0;}} a {{color:#1455a0;}}
td,th {{padding:.7rem;border-bottom:1px solid #ddd;}}
table {{width:100%;}} h1 {{margin-bottom:1.5rem;}}
</style>
</head>
<body><nav aria-label="Основная навигация">{navigation}</nav>
<main class="container rounded shadow-sm">{content}</main>
<footer class="container text-muted pb-4">Огарков Илья Евгеньевич · ЭФБО-10-24
<br>Учебный просмотр каталога. Вход пользователей пока не реализован.</footer>
</body></html>'''

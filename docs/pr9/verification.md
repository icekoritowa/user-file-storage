# ПР9 — модели и запросы

Контрольная точка: c15d99c. Исходная SQLite-база ПР7 сохранена.
Миграции library/permissions создают отдельные таблицы Django.

| Операция | Реализация |
| --- | --- |
| Список папок | Folder.select_related(owner).order_by(name) |
| Отдельная папка | get_object_or_404 по PK |
| Отдельный файл | get_object_or_404 с folder__owner |
| Файлы папки | folder.files.order_by(name, pk) |
| Занятое место владельца | File.filter(folder__owner).aggregate(Sum) |
| Поиск по нескольким полям | Q для имени файла, папки, владельца |
| Фильтры | folder_id, folder__owner_id, size__lte, uploaded_at__lte |
| Исключение пустых файлов | exclude(size=0) |
| Сортировка | name, -size, -uploaded_at, folder__owner__name с PK |
| Пагинация | Paginator, 10 записей, параметры в ссылках |
| Список прав | Access.select_related(user, folder) |
| Одно право | get_object_or_404 по folder_id/user_id |
| Пользователи | User.order_by(name).values() |
| Поиск по имени | File.filter(name__icontains, size__lte, uploaded_at__lte) |
| Права записи | Access.filter(level=write).values() |
| Файлы с владельцами | values(name, folder__name, folder__owner__name) |
| Права с именами | values(user__name, folder__name, level) |
| Общие размеры | aggregate(Count, Sum, Min, Max, Avg) |
| Квоты | User.aggregate(Count, Sum, Avg) |
| Статистика папок | annotate(Count, Sum), filter(count__gte) |
| Свободное место | Subquery по владельцу, Coalesce, F, filter(free__gte) |
| Статистика дат | values(uploaded_at).annotate(Count, Sum) |
| Пользователи без email | filter(email__isnull=True) |

Создание, изменение, удаление файлов и прав реализованы в library/services.py.
Проверки охватывают права read/write, отзыв, квоту, PROTECT, обратные связи,
импорт, сохранение ID, запрет повторного переноса в непустую базу, dumpdata/loaddata,
фильтры, сортировку, пагинацию, пустые результаты, экранирование и ошибки ввода.

Проверки: pytest — 114 passed; Django check — без замечаний;
makemigrations --check --dry-run — No changes detected; flake8 — без замечаний.
Автоматически сформированные миграции исключены только из проверки длины строк.

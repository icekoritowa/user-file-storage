"""Консольное меню с обработкой ошибок ввода и сохранения."""

import argparse
from copy import deepcopy
from pathlib import Path

from . import catalog
from .demo import main as demo
from .persistence import load_catalog, save_catalog

MENU = """
1. Пользователи          2. Добавить пользователя
3. Выбрать пользователя  4. Доступные папки
5. Создать папку         6. Файлы: поиск, отбор, сортировка
7. Добавить файл         8. Удалить файл
9. Выдать/отозвать доступ 10. Квота текущего пользователя
11. Справка о функции    0. Выход
"""


def number(prompt: str) -> int:
    """Преобразовать ввод; ValueError обрабатывается циклом меню."""
    return int(input(prompt))


def show(records: list[dict]) -> None:
    """Напечатать записи коллекции или сообщение о пустом результате."""
    if not records:
        print("Ничего не найдено.")
    for record in records:
        print(" | ".join(f"{key}: {value}" for key, value in record.items()))


def command(data: dict, user_id: int, choice: str) -> bool:
    """Выполнить команду и сообщить, изменились ли данные."""
    if choice == "1":
        show(data["users"])
    elif choice == "2":
        catalog.add_user(data, input("Имя: "), number("Квота в байтах: "))
        return True
    elif choice == "4":
        show([folder for folder in data["folders"]
              if catalog.check_access(data, user_id, folder["id"])])
    elif choice == "5":
        catalog.add_folder(data, user_id, input("Имя папки: "))
        return True
    elif choice == "6":
        query = input("Часть имени (Enter = все): ")
        maximum = input("Максимум байт (Enter = без ограничения): ")
        sort_by = input("Сортировка name/size/uploaded_at [name]: ")
        show(catalog.list_files(data, user_id, query,
                                int(maximum) if maximum else None,
                                sort_by or "name"))
    elif choice == "7":
        folder_id = number("ID папки: ")
        name = input("Имя файла: ")
        record = catalog.add_file(data, user_id, folder_id, name,
                                  number("Размер в байтах: "))
        print(f"Добавлен файл ID {record['id']} (сохранение следует далее).")
        return True
    elif choice == "8":
        catalog.delete_file(data, user_id, number("ID файла: "))
        return True
    elif choice == "9":
        folder_id = number("ID папки: ")
        target_id = number("ID получателя: ")
        catalog.set_access(data, user_id, folder_id, target_id,
                           input("Право read/write/none: ").strip())
        return True
    elif choice == "10":
        user = catalog.get_record(data, "users", user_id)
        used = catalog.used_space(data, user_id)
        print(f"Занято {used} из {user['quota']} байт. "
              f"Свободно {user['quota'] - used}.")
    elif choice == "11":
        name = input("Имя функции каталога: ")
        function = getattr(catalog, name, None)
        if name.startswith("_") or not callable(function):
            raise ValueError("Функция не найдена.")
        print(function.__doc__)
    else:
        raise ValueError("Неизвестный пункт меню.")
    return False


def run(path: Path) -> None:
    """Загрузить каталог и сохранять успешные изменения после команд."""
    try:
        data = load_catalog(path)
    except (OSError, ValueError) as error:
        print(f"Ошибка загрузки: {error}. Исходный файл не изменён.")
        return
    current_user = data["users"][0]["id"] if data["users"] else 0
    print("Система хранения пользовательских файлов — ПР2")
    try:
        while True:
            print(f"Текущий пользователь: {current_user}", MENU)
            choice = input("Выберите пункт: ").strip()
            if choice == "0":
                break
            try:
                if choice == "3":
                    new_user = number("ID пользователя: ")
                    catalog.get_record(data, "users", new_user)
                    current_user = new_user
                    continue
                # Не менять рабочее состояние, пока запись на диск не удалась.
                candidate = deepcopy(data)
                if command(candidate, current_user, choice):
                    save_catalog(path, candidate)
                    data = candidate
                    if not current_user:
                        current_user = data["users"][0]["id"]
                    print("Изменения сохранены.")
            except (ValueError, OSError) as error:
                print(f"Ошибка: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nЗавершение работы.")


def main() -> None:
    """Прочитать параметры запуска и выбрать меню или демонстрацию ПР1."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/catalog.json"))
    parser.add_argument("--demo", action="store_true", help="Сценарий ПР1")
    args = parser.parse_args()
    if args.demo:
        demo()
    else:
        run(args.data)

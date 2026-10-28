"""ПР1: моделирование загрузки пользовательского файла в папку."""

from datetime import date


MIB = 1024 * 1024


def can_write(user_name, owner_name, access):
    """Владелец и пользователь с правом write могут загружать файлы."""
    if not user_name.strip() or not owner_name.strip():
        return False
    return user_name == owner_name or access == "write"


def has_space(file_size, used_space, quota):
    """Размеры заданы целым числом байт; точное заполнение допустимо."""
    if file_size < 0 or used_space < 0 or quota < 0:
        return False
    return used_space + file_size <= quota


def upload_file(user_name, owner_name, access, folder_name, file_name,
                file_size, used_space, quota):
    """Вернуть результат учебной загрузки без записи на диск."""
    if not folder_name.strip() or not file_name.strip():
        return "Отказ: имя папки и имя файла не должны быть пустыми."
    if not can_write(user_name, owner_name, access):
        return "Отказ: нет права записи в папку."
    if not has_space(file_size, used_space, quota):
        return "Отказ: неверный размер или превышена квота хранилища."
    free_space = quota - used_space - file_size
    return (f"Загрузка разрешена: {folder_name}/{file_name}. "
            f"Останется свободно: {free_space / MIB:.2f} МиБ.")


def main():
    """Показать успешную загрузку и два варианта отказа."""
    user_name = "ilya"
    owner_name = "ilya"
    folder_name = "Учеба"
    file_name = "practice1.pdf"
    file_size = int("13107200")
    used_space = 80 * MIB
    quota = 100 * MIB
    print("Система хранения пользовательских файлов")
    print(f"Дата: {date.today().isoformat()}")
    print(f"Пользователь: {user_name}; файл: {file_name}")
    print(f"Размер: {file_size / MIB:.2f} МиБ")
    print(upload_file(user_name, owner_name, "read", folder_name,
                      file_name, file_size, used_space, quota))
    print(upload_file("guest", owner_name, "read", folder_name,
                      file_name, file_size, used_space, quota))
    print(upload_file(user_name, owner_name, "write", folder_name,
                      file_name, 21 * MIB, used_space, quota))


if __name__ == "__main__":
    main()

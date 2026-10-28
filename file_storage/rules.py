"""ПР1: моделирование загрузки пользовательского файла в папку."""

MIB = 1024 * 1024


def can_write(user_name: str, owner_name: str, access: str) -> bool:
    """Владелец и пользователь с правом write могут загружать файлы."""
    if not user_name.strip() or not owner_name.strip():
        return False
    return user_name == owner_name or access == "write"


def has_space(file_size: int, used_space: int, quota: int) -> bool:
    """Размеры заданы целым числом байт; точное заполнение допустимо."""
    if file_size < 0 or used_space < 0 or quota < 0:
        return False
    return used_space + file_size <= quota


def upload_file(user_name: str, owner_name: str, access: str,
                folder_name: str, file_name: str, file_size: int,
                used_space: int, quota: int) -> str:
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

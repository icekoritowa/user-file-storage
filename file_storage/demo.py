from datetime import date

from .rules import MIB, upload_file


def main() -> None:
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

def nonnegative(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("Размер должен быть целым неотрицательным числом.")


def valid_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Имя должно быть строкой.")
    name = name.strip()
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError("Имя пустое или содержит разделители пути.")
    return name


def positive_id(value: int) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError("ID должен быть положительным целым числом.")

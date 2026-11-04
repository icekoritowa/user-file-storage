import os
import sys


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit(
            "Для Django 5.2 нужен Python 3.10+. Используйте .venv-web.",
        )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage_web.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

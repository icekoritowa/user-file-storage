set -eu
cd "$(dirname "$0")"

if [ ! -x .venv-web/bin/python ] || ! .venv-web/bin/python -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
    selected=""
    for candidate in python3.14 python3.13 python3.12 python3.11 python3.10 python3 "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"; do
        if "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
            selected="$candidate"
            break
        fi
    done
    if [ -z "$selected" ]; then
        echo 'Для веб-версии установите Python 3.10–3.14 с https://www.python.org/downloads/macos/'
        exit 1
    fi
    "$selected" -m venv .venv-web
fi

if ! .venv-web/bin/python -c 'import django; assert django.VERSION[:2] == (5, 2)' 2>/dev/null; then
    .venv-web/bin/python -m pip install -r requirements.txt
fi
.venv-web/bin/python manage.py migrate --noinput
.venv-web/bin/python manage.py import_legacy --if-empty
.venv-web/bin/python manage.py check
exec .venv-web/bin/python manage.py runserver 127.0.0.1:8000 --insecure

import os
from pathlib import Path

import pytest

from file_storage.catalog import add_file, add_folder, add_user, empty_catalog
from file_storage.persistence import load_catalog, save_catalog


django = pytest.importorskip("django")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage_web.settings")
django.setup()


@pytest.fixture
def web(tmp_path):
    from django.test import Client, override_settings
    data = empty_catalog()
    add_user(data, "Илья", 1000)
    add_folder(data, 1, "Учеба")
    add_file(data, 1, 1, "практика.txt", 200)
    path = tmp_path / "catalog.json"
    save_catalog(path, data)
    with override_settings(CATALOG_PATH=path, DEBUG=False,
                           ALLOWED_HOSTS=["testserver"]):
        yield Client(), path


@pytest.mark.parametrize("url,text", [
    ("/", "Система хранения пользовательских файлов"),
    ("/folders/", "Учеба"),
    ("/folders/1/", "Свободно: 800"),
    ("/files/", "практика.txt"),
    ("/files/1/", "200 байт"),
    ("/accesses/", "Дополнительные права пока не выданы"),
])
def test_pages(web, url, text):
    client, path = web
    before = path.read_bytes()
    response = client.get(url)
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    body = response.content.decode()
    assert text in body and "bootstrap@5.3.3" in body
    assert '<html lang="ru">' in body
    assert '<a href="/folders/">' in body
    assert path.read_bytes() == before


@pytest.mark.parametrize("url", [
    "/unknown/", "/folders/999/", "/files/999/", "/folders/abc/",
    "/files/0/", "/files/-1/",
])
def test_custom_not_found(web, url):
    client, _ = web
    response = client.get(url)
    assert response.status_code == 404
    assert "404 — страница не найдена" in response.content.decode()
    assert "Вернуться на главную" in response.content.decode()


@pytest.mark.parametrize("url", [
    "/", "/folders/", "/folders/1/", "/files/", "/files/1/", "/accesses/",
])
def test_readonly_and_head(web, url):
    client, path = web
    before = path.read_bytes()
    assert client.post(url, {}).status_code == 405
    assert client.head(url).status_code == 200
    assert path.read_bytes() == before


def test_escaped_names_and_live_reload(web):
    client, path = web
    data = load_catalog(path)
    add_file(data, 1, 1, '<img src=x onerror="alert(1)">', 5)
    save_catalog(path, data)
    response = client.get("/files/2/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "<img src=x" not in body
    assert "&lt;img src=x" in body


def test_corrupt_json_is_preserved(web):
    client, path = web
    path.write_text("{broken")
    response = client.get("/files/")
    assert response.status_code == 503
    assert path.read_text() == "{broken"
    assert "Каталог временно недоступен" in response.content.decode()


def test_empty_catalog(web):
    client, path = web
    save_catalog(path, empty_catalog())
    assert "Файлов пока нет" in client.get("/files/").content.decode()
    assert "Папок пока нет" in client.get("/folders/").content.decode()
    assert client.get("/files/1/").status_code == 404


def test_fallback_example_and_accesses(web):
    from django.test import override_settings
    client, path = web
    path.unlink()
    example = Path(__file__).resolve().parents[1] / "data/example.json"
    with override_settings(EXAMPLE_PATH=example):
        assert "practice1.pdf" in client.get("/files/").content.decode()
        assert "guest" in client.get("/accesses/").content.decode()
    assert not path.exists()


def test_url_names_and_converter():
    from django.urls import resolve, reverse
    assert reverse("library:file_detail", args=[7]) == "/files/7/"
    assert resolve("/folders/5/").kwargs == {"folder_id": 5}


def test_disallowed_host(web):
    client, _ = web
    assert client.get("/", HTTP_HOST="invalid.example").status_code == 400


@pytest.mark.parametrize("level,label,description", [
    ("read", "read — только чтение", "может просматривать файлы"),
    ("write", "write — чтение и запись", "добавлять и удалять файлы"),
])
def test_access_details_and_revocation(web, level, label, description):
    from file_storage.catalog import set_access
    client, path = web
    data = load_catalog(path)
    add_user(data, "Гость", 1000)
    set_access(data, 1, 1, 2, level)
    save_catalog(path, data)
    before = path.read_bytes()
    listing = client.get("/accesses/").content.decode()
    assert 'href="/accesses/1/2/"' in listing
    assert label in listing
    response = client.get("/accesses/1/2/")
    assert response.status_code == 200
    body = response.content.decode()
    assert label in body and description in body
    assert 'href="/folders/1/"' in body
    assert "Гость" in body and "Илья" in body
    assert client.head("/accesses/1/2/").status_code == 200
    assert client.post("/accesses/1/2/", {}).status_code == 405
    assert path.read_bytes() == before
    set_access(data, 1, 1, 2, "none")
    save_catalog(path, data)
    assert client.get("/accesses/1/2/").status_code == 404


@pytest.mark.parametrize("url", [
    "/accesses/999/2/", "/accesses/1/999/", "/accesses/abc/2/",
])
def test_missing_access(web, url):
    client, _ = web
    response = client.get(url)
    assert response.status_code == 404
    assert "404 — страница не найдена" in response.content.decode()


def test_folder_contents_and_template_formatting(web):
    client, path = web
    data = load_catalog(path)
    add_folder(data, 1, "Пустая папка")
    save_catalog(path, data)
    item = data["files"][0]
    body = client.get("/folders/1/").content.decode()
    assert "Всего файлов: 1" in body
    assert 'href="/files/1/"' in body
    assert item.uploaded_at.strftime("%d.%m.%Y") in body
    empty = client.get("/folders/2/").content.decode()
    assert "Файлов пока нет" in empty
    assert "практика.txt" not in empty
    assert "Всего папок: 2" in client.get("/folders/").content.decode()


def test_shared_templates_and_static_assets(web):
    from django.contrib.staticfiles import finders
    from django.test.utils import (
        setup_test_environment, teardown_test_environment,
    )
    client, _ = web
    setup_test_environment()
    try:
        response = client.get("/folders/")
        names = {t.name for t in response.templates}
        assert {
            "base.html", "includes/navigation.html",
            "library/folder_list.html", "library/includes/folder_card.html",
        } <= names
        assert response.context["folders"][0].name == "Учеба"
    finally:
        teardown_test_environment()
    for asset in ["css/style.css", "js/main.js", "img/logo.svg"]:
        assert finders.find("homepage/" + asset)
        assert f'/static/homepage/{asset}' in response.content.decode()


def test_escaping_in_folder_and_access_templates(web):
    from file_storage.catalog import set_access
    client, path = web
    data = load_catalog(path)
    name = '<img src=x onerror="alert(1)">'
    add_user(data, name, 1000)
    add_folder(data, 1, name)
    set_access(data, 1, 2, 2, "write")
    save_catalog(path, data)
    for url in ["/folders/", "/folders/2/", "/accesses/", "/accesses/2/2/"]:
        body = client.get(url).content.decode()
        assert name not in body
        assert "&lt;img src=x" in body

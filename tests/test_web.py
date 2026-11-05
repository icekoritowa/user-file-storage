import os
from io import StringIO

import pytest

from db.database import ROOT


django = pytest.importorskip("django")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "storage_web.settings")
django.setup()


@pytest.fixture(scope="module")
def orm_database():
    from django.test.utils import setup_databases, teardown_databases
    config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(config, verbosity=0)


@pytest.fixture
def web(orm_database):
    from django.core.management import call_command
    from django.test import Client, override_settings
    call_command("flush", verbosity=0, interactive=False)
    call_command("import_legacy", source=ROOT / "data/storage.sqlite",
                 stdout=StringIO())
    with override_settings(ALLOWED_HOSTS=["testserver"], DEBUG=False):
        yield Client()


@pytest.mark.parametrize("url", [
    "/", "/folders/", "/folders/1/", "/files/", "/files/1/",
    "/accesses/", "/accesses/1/2/", "/statistics/",
])
def test_pages_and_methods(web, url):
    response = web.get(url)
    assert response.status_code == 200
    assert b"bootstrap@5.3.3" in response.content
    assert b"/static/homepage/css/style.css" in response.content
    assert web.head(url).status_code == 200
    assert web.post(url).status_code == 405


@pytest.mark.parametrize("url", [
    "/unknown/", "/files/999/", "/folders/999/", "/accesses/1/999/",
    "/files/abc/", "/files/-1/",
])
def test_missing(web, url):
    response = web.get(url)
    assert response.status_code == 404
    assert "404 — страница не найдена" in response.content.decode()


@pytest.mark.parametrize("params", [
    {"size": "-1"}, {"owner": "bad"}, {"date": "2026-02-30"},
    {"sort": "__class__"}, {"folder": "9999999999999999999999"},
])
def test_invalid_filters(web, params):
    assert web.get("/files/", params).status_code == 400


def test_search_sort_pagination(web):
    from library.models import File
    for i in range(25):
        File.objects.create(name=f"test{i:02}.txt", folder_id=1, size=i)
    response = web.get("/files/", {
        "q": "test", "sort": "size", "nonempty": "1", "page": "2",
    })
    body = response.content.decode()
    assert "test14.txt" in body and "test24.txt" not in body
    assert "q=test" in body and "sort=size" in body
    assert "page=3" in body and "nonempty=1" in body
    assert web.get("/files/", {"page": "bad"}).status_code == 200
    assert web.get("/files/", {"page": "999"}).status_code == 200
    body = web.get("/files/", {"owner": "2"}).content.decode()
    assert "Файлов пока нет" in body
    body = web.get("/files/", {"q": "Личное"}).content.decode()
    assert "notes.txt" in body and "practice1.pdf" not in body


def test_statistics_and_quota(web):
    from library.models import File
    from django.test.utils import (
        setup_test_environment, teardown_test_environment,
    )
    setup_test_environment()
    try:
        response = web.get("/statistics/", {"size": "0"})
        sections = {s["title"]: s for s in response.context["sections"]}
        assert sections["Объём файлов"]["rows"][0][:2] == [2, 13108224]
        free = sections["Папки со свободным местом"]["rows"]
        assert len(free) == 2
        assert all(row[2] == 104857600 - 13108224 for row in free)
        File.objects.all().delete()
        response = web.get("/statistics/")
        sections = {s["title"]: s for s in response.context["sections"]}
        assert sections["Объём файлов"]["rows"][0][:2] == [0, 0]
    finally:
        teardown_test_environment()
    for params in [{"size": "-1"}, {"date": "bad"}, {"offset": "bad"}]:
        assert web.get("/statistics/", params).status_code == 400


def test_crud_rules_and_relations(web):
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.db.models.deletion import ProtectedError
    from library.models import File, Folder, User
    from library.services import delete_file, save_file, set_access
    from permissions.models import Access
    owner = User.objects.get(pk=1)
    guest = User.objects.get(pk=2)
    folder = Folder.objects.get(pk=1)
    assert folder.owner == owner
    assert guest.shared_folders.get(pk=1) == folder
    with pytest.raises(PermissionDenied):
        save_file(File(name="new", folder=folder, size=1), guest.pk)
    set_access(folder, guest, "write", owner.pk)
    file = save_file(File(name="new", folder=folder, size=1), guest.pk)
    file.name = "renamed"
    save_file(file, owner.pk)
    assert File.objects.get(pk=file.pk).name == "renamed"
    with pytest.raises(ValidationError):
        save_file(File(name="huge", folder=folder, size=owner.quota), owner.pk)
    with pytest.raises(ProtectedError):
        folder.delete()
    delete_file(file.pk, guest.pk)
    assert not File.objects.filter(pk=file.pk).exists()
    with pytest.raises(PermissionDenied):
        set_access(folder, guest, "none", guest.pk)
    set_access(folder, guest, "none", owner.pk)
    assert not Access.objects.filter(folder=folder, user=guest).exists()


def test_import_preserves_ids_and_refuses_overwrite(web):
    from django.core.management import call_command
    from django.core.management.base import CommandError
    from library.models import File
    source = ROOT / "data/storage.sqlite"
    before = source.read_bytes()
    with pytest.raises(CommandError):
        call_command("import_legacy", source=source)
    call_command("import_legacy", source=source, if_empty=True,
                 stdout=StringIO())
    assert source.read_bytes() == before
    file = File.objects.select_related("folder__owner").get(pk=1)
    assert file.folder_id == 1 and file.folder.owner_id == 1
    assert file.name == "practice1.pdf"


def test_escaping_and_live_updates(web):
    from library.models import File
    File.objects.filter(pk=1).update(name='<img src=x onerror="alert(1)">')
    body = web.get("/files/1/").content.decode()
    assert "&lt;img src=x" in body and "<img src=x" not in body
    assert web.get("/files/", {"q": "' OR 1=1 --"}).status_code == 200


def test_dump_and_load(web, tmp_path):
    from django.core.management import call_command
    from library.models import File
    target = tmp_path / "fixture.json"
    with target.open("w") as stream:
        call_command("dumpdata", "library", "permissions", stdout=stream)
    call_command("flush", interactive=False, verbosity=0)
    call_command("loaddata", str(target), verbosity=0)
    assert File.objects.get(pk=1).folder.owner.name == "ilya"

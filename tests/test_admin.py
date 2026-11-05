import pytest


@pytest.fixture
def admin_client(web):
    from django.contrib.auth import get_user_model
    admin = get_user_model().objects.create_superuser(
        username="test-admin", password="test-admin-password",
    )
    web.force_login(admin)
    return web


@pytest.mark.parametrize("url", [
    "/admin/", "/admin/library/user/", "/admin/library/folder/",
    "/admin/library/file/", "/admin/permissions/access/",
    "/admin/library/user/1/change/", "/admin/library/folder/1/change/",
    "/admin/library/file/add/", "/admin/permissions/access/add/",
])
def test_admin_pages(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_admin_requires_staff(web):
    from django.contrib.auth import get_user_model
    assert web.get("/admin/").status_code == 302
    account = get_user_model().objects.create_user(username="visitor")
    web.force_login(account)
    assert web.get("/admin/").status_code == 302
    account.is_staff = True
    account.save()
    assert web.get("/admin/library/file/").status_code == 403


def test_admin_file_crud_and_validation(admin_client):
    from library.models import File
    payload = {"name": "admin.txt", "folder": 1, "size": 123,
               "uploaded_at": "2026-11-05", "_save": "Сохранить"}
    assert admin_client.post("/admin/library/file/add/", payload).status_code \
        == 302
    file = File.objects.get(name="admin.txt")
    assert "admin.txt" in admin_client.get("/files/").content.decode()
    payload["size"] = 999999999
    response = admin_client.post(
        f"/admin/library/file/{file.pk}/change/", payload,
    )
    assert response.status_code == 200
    assert "Превышена квота" in response.content.decode()
    file.refresh_from_db()
    assert file.size == 123
    payload.update(name="changed.txt", size=10)
    assert admin_client.post(
        f"/admin/library/file/{file.pk}/change/", payload,
    ).status_code == 302
    file.refresh_from_db()
    assert file.name == "changed.txt"
    assert admin_client.post(
        f"/admin/library/file/{file.pk}/delete/", {"post": "yes"},
    ).status_code == 302
    assert not File.objects.filter(pk=file.pk).exists()


def test_admin_access_validation(admin_client):
    response = admin_client.post("/admin/permissions/access/add/", {
        "user": 1, "folder": 1, "level": "write", "_save": "Сохранить",
    })
    assert response.status_code == 200
    assert "Владельцу не нужно" in response.content.decode()


def test_slug_generated_field_and_context(web):
    from library.models import File, Folder
    from permissions.models import Access
    first = Folder.objects.create(name="Одинаковая", owner_id=1)
    second = Folder.objects.create(name="Одинаковая", owner_id=2)
    assert first.slug != second.slug
    assert web.get(first.get_absolute_url()).status_code == 200
    assert web.get("/folders/by-name/missing/").status_code == 404
    file = File.objects.get(pk=1)
    assert file.is_large is True
    File.objects.filter(pk=file.pk).update(size=1)
    file.refresh_from_db()
    assert file.is_large is False
    assert Access.objects.readable().count() == 1
    assert Access.objects.writable().count() == 0
    assert "Файловое хранилище" in web.get("/").content.decode()


def test_optimized_related_queries(web):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from library.models import File
    for i in range(10):
        File.objects.create(name=f"query{i}", folder_id=1, size=1)
    with CaptureQueriesContext(connection) as unoptimized:
        list((f.name, f.folder.owner.name) for f in File.objects.all())
    with CaptureQueriesContext(connection) as optimized:
        list((f.name, f.folder.owner.name) for f in File.objects.with_owners())
    assert len(unoptimized) == 25
    assert len(optimized) == 1


def test_admin_folder_and_user_creation(admin_client):
    from library.models import Folder, User
    response = admin_client.post("/admin/library/user/add/", {
        "name": "Новый", "quota": 1000, "email": "", "_save": "Сохранить",
    })
    assert response.status_code == 302
    user = User.objects.get(name="Новый")
    response = admin_client.post("/admin/library/folder/add/", {
        "name": "Новая папка", "owner": user.pk, "_save": "Сохранить",
    })
    assert response.status_code == 302
    folder = Folder.objects.get(name="Новая папка")
    assert admin_client.get(folder.get_absolute_url()).status_code == 200

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from file_storage.catalog import get_record, used_space
from homepage.data import catalog_view


def find(data: dict, collection: str, identifier: int):
    try:
        return get_record(data, collection, identifier)
    except ValueError as error:
        raise Http404("Объект не найден") from error


@catalog_view
def folders(request: HttpRequest, data: dict) -> HttpResponse:
    return render(request, "library/folder_list.html", {
        "folders": data["folders"],
    })


@catalog_view
def folder_detail(request: HttpRequest, data: dict,
                  folder_id: int) -> HttpResponse:
    folder = find(data, "folders", folder_id)
    used = used_space(data, folder.owner.id)
    context = {
        "folder": folder,
        "used": used,
        "free": folder.owner.quota - used,
        "files": [f for f in data["files"] if f.folder is folder],
    }
    return render(request, "library/folder_detail.html", context)


@catalog_view
def files(request: HttpRequest, data: dict) -> HttpResponse:
    return render(request, "library/file_list.html", {
        "files": data["files"],
    })


@catalog_view
def file_detail(request: HttpRequest, data: dict,
                file_id: int) -> HttpResponse:
    return render(request, "library/file_detail.html", {
        "file": find(data, "files", file_id),
    })

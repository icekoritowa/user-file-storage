from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from homepage.data import catalog_view


@catalog_view
def accesses(request: HttpRequest, data: dict) -> HttpResponse:
    return render(request, "permissions/access_list.html", {
        "accesses": data["accesses"],
    })


@catalog_view
def access_detail(request: HttpRequest, data: dict,
                  folder_id: int, user_id: int) -> HttpResponse:
    access = next((a for a in data["accesses"]
                   if a.folder.id == folder_id and a.user.id == user_id), None)
    if access is None:
        raise Http404("Право доступа не найдено")
    return render(request, "permissions/access_detail.html", {
        "access": access,
    })

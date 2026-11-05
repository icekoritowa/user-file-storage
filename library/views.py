from datetime import date

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render

from homepage.data import database_view
from .models import File, Folder

SORTS = {
    "name": ("name", "pk"),
    "size": ("-size", "pk"),
    "date": ("-uploaded_at", "pk"),
    "owner": ("folder__owner__name", "name", "pk"),
}


@database_view
def folders(request):
    return render(request, "library/folder_list.html", {
        "folders": Folder.objects.select_related("owner").order_by("name"),
    })


@database_view
def folder_detail(request, folder_id):
    folder = get_object_or_404(
        Folder.objects.select_related("owner"), pk=folder_id,
    )
    used = File.objects.filter(folder__owner=folder.owner).aggregate(
        total=Sum("size", default=0),
    )["total"]
    return render(request, "library/folder_detail.html", {
        "folder": folder, "used": used, "free": folder.owner.quota - used,
        "files": folder.files.order_by("name", "pk"),
    })


@database_view
def files(request):
    records = File.objects.select_related("folder__owner")
    params = request.GET
    sort = params.get("sort", "name")
    try:
        if sort not in SORTS:
            raise ValueError
        for key, field in (("folder", "folder_id"),
                           ("owner", "folder__owner_id"),
                           ("size", "size__lte")):
            if params.get(key):
                value = int(params[key])
                if value < 0 or value > 9223372036854775807:
                    raise ValueError
                records = records.filter(**{field: value})
        if params.get("date"):
            records = records.filter(
                uploaded_at__lte=date.fromisoformat(params["date"]),
            )
    except ValueError:
        return render(request, "library/file_list.html", {
            "error": "Проверьте фильтры и сортировку.",
        }, status=400)
    if params.get("q"):
        records = records.filter(
            Q(name__icontains=params["q"])
            | Q(folder__name__icontains=params["q"])
            | Q(folder__owner__name__icontains=params["q"]),
        )
    if params.get("nonempty") == "1":
        records = records.exclude(size=0)
    page = Paginator(records.order_by(*SORTS[sort]), 10).get_page(
        params.get("page"),
    )
    query = params.copy()
    query.pop("page", None)
    return render(request, "library/file_list.html", {
        "files": page.object_list, "page_obj": page,
        "query": query.urlencode(), "filters": params,
    })


@database_view
def file_detail(request, file_id):
    return render(request, "library/file_detail.html", {
        "file": get_object_or_404(
            File.objects.select_related("folder__owner"), pk=file_id,
        ),
    })

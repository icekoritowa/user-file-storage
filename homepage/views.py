from django.shortcuts import render

from library.models import File, Folder, User
from permissions.models import Access
from .data import database_view


@database_view
def index(request):
    return render(request, "homepage/index.html", {
        "users_count": User.objects.count(),
        "folders_count": Folder.objects.count(),
        "files_count": File.objects.count(),
        "accesses_count": Access.objects.count(),
    })


def page_not_found(request, exception):
    return render(request, "404.html", status=404)

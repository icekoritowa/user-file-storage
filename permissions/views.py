from django.shortcuts import get_object_or_404, render

from homepage.data import database_view
from .models import Access


@database_view
def accesses(request):
    return render(request, "permissions/access_list.html", {
        "accesses": Access.objects.with_names(),
    })


@database_view
def access_detail(request, folder_id, user_id):
    return render(request, "permissions/access_detail.html", {
        "access": get_object_or_404(
            Access.objects.with_names(),
            folder_id=folder_id, user_id=user_id,
        ),
    })

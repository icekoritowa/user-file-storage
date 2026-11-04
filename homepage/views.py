from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .data import catalog_view


@catalog_view
def index(request: HttpRequest, data: dict) -> HttpResponse:
    return render(request, "homepage/index.html", data)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "404.html", status=404)

from django.urls import include, path

from db.views import statistics

urlpatterns = [
    path("statistics/", statistics, name="statistics"),
    path("", include("homepage.urls")),
    path("", include("library.urls")),
    path("accesses/", include("permissions.urls")),
]
handler404 = "homepage.views.page_not_found"

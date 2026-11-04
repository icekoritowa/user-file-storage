from django.urls import include, path

urlpatterns = [
    path("", include("homepage.urls")),
    path("", include("library.urls")),
    path("accesses/", include("permissions.urls")),
]
handler404 = "homepage.views.page_not_found"

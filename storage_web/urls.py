from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from db.views import statistics

urlpatterns = [
    path("admin/", admin.site.urls),
    path("statistics/", statistics, name="statistics"),
    path("", include("homepage.urls")),
    path("", include("library.urls")),
    path("accesses/", include("permissions.urls")),
]
handler404 = "homepage.views.page_not_found"

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]

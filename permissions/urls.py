from django.urls import path

from . import views

app_name = "permissions"
urlpatterns = [
    path("", views.accesses, name="accesses"),
    path("<int:folder_id>/<int:user_id>/", views.access_detail,
         name="access_detail"),
]

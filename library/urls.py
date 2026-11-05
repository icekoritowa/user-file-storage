from django.urls import path

from . import views

app_name = "library"
urlpatterns = [
    path("folders/", views.folders, name="folders"),
    path("folders/<int:folder_id>/", views.folder_detail,
         name="folder_detail"),
    path("files/", views.files, name="files"),
    path("files/<int:file_id>/", views.file_detail, name="file_detail"),
]

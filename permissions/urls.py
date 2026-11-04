from django.urls import path

from . import views

app_name = "permissions"
urlpatterns = [path("", views.accesses, name="accesses")]

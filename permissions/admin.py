from django.contrib import admin

from .models import Access


@admin.register(Access)
class AccessAdmin(admin.ModelAdmin):
    list_display = ("user", "folder", "level")
    list_filter = ("level", "folder")
    search_fields = ("user__name", "folder__name")
    list_select_related = ("user", "folder")
    autocomplete_fields = ("user", "folder")
    ordering = ("folder__name", "user__name")

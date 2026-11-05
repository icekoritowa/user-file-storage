from django.contrib import admin

from library.models import File, Folder, User
from permissions.models import Access


class ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class FileInline(ReadOnlyInline):
    model = File
    fields = ("name", "size", "uploaded_at", "is_large")
    readonly_fields = fields


class FolderInline(ReadOnlyInline):
    model = Folder
    fields = ("name", "slug")
    readonly_fields = fields


class AccessInline(ReadOnlyInline):
    model = Access
    fields = ("user", "folder", "level")
    readonly_fields = fields

    def get_queryset(self, request):
        return super().get_queryset(request).with_names()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "quota")
    search_fields = ("name", "email")
    list_filter = ("quota",)
    ordering = ("name", "pk")
    inlines = (FolderInline, AccessInline)

    def get_inlines(self, request, obj=None):
        return self.inlines if obj else ()


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "slug")
    search_fields = ("name", "owner__name", "slug")
    list_filter = ("owner",)
    list_select_related = ("owner",)
    ordering = ("name", "pk")
    autocomplete_fields = ("owner",)
    inlines = (FileInline, AccessInline)
    readonly_fields = ("slug",)

    def get_inlines(self, request, obj=None):
        return self.inlines if obj else ()

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields + (("owner",) if obj else ())


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "folder", "owner", "size",
                    "uploaded_at", "is_large")
    search_fields = ("name", "folder__name", "folder__owner__name")
    list_filter = ("is_large", "uploaded_at", "folder")
    list_select_related = ("folder__owner",)
    ordering = ("-uploaded_at", "pk")
    autocomplete_fields = ("folder",)
    readonly_fields = ("is_large",)
    date_hierarchy = "uploaded_at"

    @admin.display(description="Владелец", ordering="folder__owner__name")
    def owner(self, obj):
        return obj.folder.owner


admin.site.site_header = "Управление файловым хранилищем"
admin.site.site_title = "Файловое хранилище"
admin.site.index_title = "Данные и права доступа"

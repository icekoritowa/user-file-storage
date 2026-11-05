from datetime import date

from django.db.models import (
    Avg, BigIntegerField, Count, F, Max, Min, OuterRef, Subquery, Sum,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render

from homepage.data import database_view
from library.models import File, Folder, User
from permissions.models import Access


def section(title, rows, columns):
    return {"title": title, "columns": columns,
            "rows": [[row[c] for c in columns] for row in rows]}


@database_view
def statistics(request):
    try:
        values = {
            "size": int(request.GET.get("size", "104857600")),
            "date": date.fromisoformat(request.GET.get(
                "date", date.today().isoformat())).isoformat(),
            "offset": int(request.GET.get("offset", "0")),
            "minimum": int(request.GET.get("minimum", "0")),
        }
        if any(not 0 <= values[k] <= 9223372036854775807
               for k in ("size", "offset", "minimum")):
            raise ValueError
    except ValueError:
        return render(request, "db/statistics.html", {
            "error": "Введите дату и неотрицательные целые числа.",
        }, status=400)
    q = request.GET.get("q", "")
    offset = values["offset"]
    used = File.objects.filter(folder__owner_id=OuterRef("owner_id")).order_by(
    ).values("folder__owner_id").annotate(total=Sum("size")).values("total")
    free = Folder.objects.annotate(free=F("owner__quota") - Coalesce(
        Subquery(used, output_field=BigIntegerField()), 0,
        output_field=BigIntegerField(),
    )).filter(free__gte=values["size"]).order_by("-free", "pk")
    totals = File.objects.aggregate(
        count=Count("id"), total=Sum("size", default=0), minimum=Min("size"),
        maximum=Max("size"), average=Avg("size"),
    )
    quotas = User.objects.aggregate(
        users=Count("id"), total_quota=Sum("quota", default=0),
        average_quota=Avg("quota"),
    )
    sections = [
        section("Пользователи", User.objects.order_by("name").values(),
                ["id", "name", "quota", "email"]),
        section("Папки", Folder.objects.order_by("name").values(),
                ["id", "name", "owner_id"]),
        section("Поиск файлов", File.objects.filter(
            name__icontains=q, size__lte=values["size"],
            uploaded_at__lte=values["date"],
        ).order_by("-size", "pk").values()[offset:offset + 20],
            ["name", "size", "uploaded_at"]),
        section("Права записи", Access.objects.writable().values(),
                ["user_id", "folder_id"]),
        section("Файлы и владельцы", File.objects.values(
            "name", "folder__name", "folder__owner__name",
        ), ["name", "folder__name", "folder__owner__name"]),
        section("Выданный доступ", Access.objects.values(
            "user__name", "folder__name", "level",
        ), ["user__name", "folder__name", "level"]),
        section("Объём файлов", [totals], list(totals)),
        section("Квоты", [quotas], list(quotas)),
        section("Файлы по папкам", Folder.objects.annotate(
            count=Count("files"), bytes=Sum("files__size", default=0),
        ).filter(count__gte=values["minimum"]).order_by(
            "-count", "pk",
        ).values("name", "count", "bytes"), ["name", "count", "bytes"]),
        section("Папки со свободным местом", free.values(
            "name", "owner__name", "free",
        ), ["name", "owner__name", "free"]),
        section("Файлы по датам", File.objects.values("uploaded_at").annotate(
            count=Count("id"), bytes=Sum("size"),
        ).order_by("-uploaded_at"), ["uploaded_at", "count", "bytes"]),
        section("Пользователи без email", User.objects.filter(
            email__isnull=True,
        ).order_by("name").values("name"), ["name"]),
    ]
    return render(request, "db/statistics.html", {
        "sections": sections, "values": values, "q": q,
    })

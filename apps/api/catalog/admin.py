"""Curator-facing admin for the archive."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Collection, Format, Video, VideoFormat


@admin.register(Collection)
class CollectionAdmin(ModelAdmin):
    list_display = ["title", "slug", "order", "video_count"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title", "slug"]

    @admin.display(description="jumlah video")
    def video_count(self, obj) -> int:
        return obj.videos.count()


@admin.register(Format)
class FormatAdmin(ModelAdmin):
    list_display = ["name", "video_count"]
    search_fields = ["name"]

    @admin.display(description="dipakai oleh")
    def video_count(self, obj) -> int:
        return obj.videos.count()


class VideoFormatInline(TabularInline):
    model = VideoFormat
    extra = 1
    autocomplete_fields = ["format"]
    ordering = ["position"]


@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = [
        "title",
        "artist",
        "collection",
        "customary_region",
        "is_published",
        "is_featured",
    ]
    list_filter = [
        "is_published",
        "is_featured",
        "collection",
        "customary_region",
        "formats",
    ]
    list_editable = ["is_published", "is_featured"]
    search_fields = ["title", "artist", "language", "region", "note"]
    prepopulated_fields = {"slug": ("title", "artist")}
    autocomplete_fields = ["collection"]
    inlines = [VideoFormatInline]
    readonly_fields = ["created_at", "updated_at"]
    list_per_page = 50

    fieldsets = (
        ("Identitas", {"fields": ("title", "artist", "slug", "youtube_id")}),
        (
            "Penempatan",
            {
                "fields": ("collection", "position"),
                "description": (
                    "Bentuk video diatur di tabel bawah. Yang paling atas "
                    "menjadi label di kartu video."
                ),
            },
        ),
        (
            "Asal & bahasa",
            {"fields": ("region", "customary_region", "language")},
        ),
        ("Sumber", {"fields": ("year", "duration")}),
        (
            "Naskah kurasi",
            {
                "fields": ("note", "description", "context"),
                "description": "Tulis yang belum pasti apa adanya.",
            },
        ),
        (
            "Tampil",
            {
                "fields": ("is_published", "is_featured"),
                "description": "Peringkat ditentukan kurator, bukan jumlah tontonan.",
            },
        ),
        ("Jejak", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("collection")

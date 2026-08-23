"""Read-only catalogue endpoints.

`ReadOnlyModelViewSet` registers no write routes, so PATCH and DELETE are 405
from the router.
"""

from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import Collection, Video
from .recommendations import related_slug_map
from .serializers import CollectionSerializer, VideoSerializer


class VideoFilter(filters.FilterSet):
    collection = filters.CharFilter(field_name="collection__slug")
    format = filters.CharFilter(field_name="formats__name")

    class Meta:
        model = Video
        fields = {
            "customary_region": ["exact"],
            "language": ["exact"],
            "year": ["exact"],
            "is_featured": ["exact"],
        }


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """The shelves, in curator-defined order."""

    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    lookup_field = "slug"


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Published videos. Drafts stay hidden until `is_published` is set."""

    serializer_class = VideoSerializer
    lookup_field = "slug"
    filterset_class = VideoFilter
    ordering_fields = ["position", "title", "year", "created_at"]

    def get_queryset(self):
        return (
            Video.published.select_related("collection")
            .prefetch_related("video_formats__format")
            .all()
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Scored over every published video, not the filtered page.
        context["related_map"] = related_slug_map(
            Video.published.prefetch_related("video_formats__format").all()
        )
        return context

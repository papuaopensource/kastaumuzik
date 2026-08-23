"""Read serializers for the catalogue.

Field names are snake_case; `apps/web/src/lib/catalog.ts` maps them to the
camelCase shape the pages use.
"""

from rest_framework import serializers

from .models import Collection, Video


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["slug", "title", "order"]


class VideoSerializer(serializers.ModelSerializer):
    collection = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    # Read through the join rows to keep curator order; a SlugRelatedField
    # would sort by Format.Meta.ordering.
    formats = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "slug",
            "title",
            "artist",
            "youtube_id",
            "collection",
            "region",
            "customary_region",
            "language",
            "formats",
            "year",
            "duration",
            "note",
            "description",
            "context",
            "is_featured",
            "related",
        ]

    def get_formats(self, obj) -> list[str]:
        return obj.ordered_formats

    def get_related(self, obj) -> list[str]:
        """Ranked slugs of related videos, from the map the viewset supplies."""
        return self.context.get("related_map", {}).get(obj.slug, [])

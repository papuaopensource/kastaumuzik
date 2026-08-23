"""Ranking of related videos.

`related` ships as a field on the video list, so the frontend build needs one
request rather than one per page.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import CustomaryRegion

WEIGHT_LANGUAGE = 4
WEIGHT_CUSTOMARY_REGION = 3
WEIGHT_FORMAT = 1

RELATED_LIMIT = 10

# Regions that record missing information rather than name a real place. Two
# videos sharing one of these are not related.
UNSPECIFIC_REGIONS = frozenset(
    {CustomaryRegion.UNCONFIRMED.value, CustomaryRegion.CROSS_REGION.value}
)


class _Facets:
    """Facets of one video, read once so scoring does not re-query."""

    __slots__ = ("slug", "title", "language", "customary_region", "formats")

    def __init__(self, video) -> None:
        self.slug = video.slug
        self.title = video.title
        self.language = video.language
        self.customary_region = video.customary_region
        # Relies on prefetch_related; otherwise a query per video.
        self.formats = frozenset(video.ordered_formats)


def _score(source: _Facets, candidate: _Facets) -> int:
    score = 0

    if source.language and source.language == candidate.language:
        score += WEIGHT_LANGUAGE

    if (
        source.customary_region not in UNSPECIFIC_REGIONS
        and source.customary_region == candidate.customary_region
    ):
        score += WEIGHT_CUSTOMARY_REGION

    score += len(source.formats & candidate.formats) * WEIGHT_FORMAT

    return score


def related_slug_map(videos: Iterable, limit: int = RELATED_LIMIT) -> dict[str, list[str]]:
    """Map every video's slug to its ranked related slugs.

    Computed for the whole set in one pass. Ties break on title, so the order is
    stable between builds.
    """

    facets = [_Facets(video) for video in videos]

    ranked: dict[str, list[str]] = {}
    for source in facets:
        candidates = [other for other in facets if other.slug != source.slug]
        candidates.sort(key=lambda other: (-_score(source, other), other.title))
        ranked[source.slug] = [other.slug for other in candidates[:limit]]

    return ranked

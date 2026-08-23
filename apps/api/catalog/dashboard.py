"""Data for the admin home page.

Wired up through `UNFOLD["DASHBOARD_CALLBACK"]`. Everything here answers one of
two questions a curator arrives with: what is waiting for me, and where is the
archive still thin.
"""

from __future__ import annotations

import json
from datetime import timedelta

from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from submissions.models import Submission, SubmissionStatus

from .models import Collection, CustomaryRegion, Video

# How many months the submissions trend covers.
TREND_MONTHS = 6

# How many pending submissions the shortlist shows.
PENDING_PREVIEW = 5

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
]

PENDING_STATUSES = [SubmissionStatus.NEW, SubmissionStatus.IN_REVIEW]


def _chart(labels: list[str], data: list[int], label: str) -> str:
    """Serialise one dataset into the shape Unfold's chart component expects."""
    return json.dumps(
        {
            "labels": labels,
            "datasets": [
                {
                    "label": label,
                    "data": data,
                    "backgroundColor": "var(--color-primary-500)",
                    "borderColor": "var(--color-primary-500)",
                    "borderRadius": 4,
                    "borderWidth": 2,
                    "tension": 0.3,
                    "displayYAxis": True,
                }
            ],
        }
    )


def _videos_per_collection() -> str:
    # Published only, matching the region chart; drafts have their own KPI.
    rows = (
        Collection.objects.annotate(
            total=Count("videos", filter=Q(videos__is_published=True))
        )
        .order_by("order", "slug")
        .values_list("title", "total")
    )
    return _chart([title for title, _ in rows], [total for _, total in rows], "Video")


def _videos_per_region() -> str:
    counts = dict(
        Video.published.values_list("customary_region")
        .annotate(total=Count("id"))
        .values_list("customary_region", "total")
    )
    # Every customary region is listed even at zero: a gap in coverage is
    # something the archive should show, not hide.
    labels = [region.label for region in CustomaryRegion]
    data = [counts.get(region.value, 0) for region in CustomaryRegion]
    return _chart(labels, data, "Video terbit")


def _submissions_trend() -> str:
    today = timezone.localdate().replace(day=1)

    months = []
    cursor = today
    for _ in range(TREND_MONTHS):
        months.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    months.reverse()

    counts = []
    for index, start in enumerate(months):
        end = months[index + 1] if index + 1 < len(months) else None
        window = Submission.objects.filter(created_at__date__gte=start)
        if end:
            window = window.filter(created_at__date__lt=end)
        counts.append(window.count())

    labels = [f"{MONTH_NAMES[month.month - 1]} {month.year % 100:02d}" for month in months]
    return _chart(labels, counts, "Usulan masuk")


def callback(request, context):
    published = Video.published.count()
    drafts = Video.objects.filter(is_published=False).count()
    pending = Submission.objects.filter(status__in=PENDING_STATUSES).count()
    unconfirmed_region = Video.published.filter(
        customary_region=CustomaryRegion.UNCONFIRMED
    ).count()

    submissions_url = reverse("admin:submissions_submission_changelist")
    videos_url = reverse("admin:catalog_video_changelist")

    context.update(
        {
            "kpi": [
                {
                    "title": "Usulan menunggu tinjauan",
                    "value": pending,
                    "icon": "inbox",
                    "href": (
                        f"{submissions_url}?status__in="
                        f"{SubmissionStatus.NEW},{SubmissionStatus.IN_REVIEW}"
                    ),
                },
                {
                    "title": "Video terbit",
                    "value": published,
                    "icon": "music_video",
                    "href": f"{videos_url}?is_published__exact=1",
                },
                {
                    "title": "Draft belum terbit",
                    "value": drafts,
                    "icon": "edit_note",
                    "href": f"{videos_url}?is_published__exact=0",
                },
                {
                    "title": "Wilayah adat belum dipastikan",
                    "value": unconfirmed_region,
                    "icon": "help",
                    "href": (
                        f"{videos_url}?customary_region__exact="
                        f"{CustomaryRegion.UNCONFIRMED.value}"
                    ),
                },
            ],
            "collection_chart": _videos_per_collection(),
            "region_chart": _videos_per_region(),
            "submissions_chart": _submissions_trend(),
            "pending_submissions": (
                Submission.objects.filter(status__in=PENDING_STATUSES)
                .order_by("-created_at")[:PENDING_PREVIEW]
            ),
            "submissions_url": submissions_url,
        }
    )

    return context

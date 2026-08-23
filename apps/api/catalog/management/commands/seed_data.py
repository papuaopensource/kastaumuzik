"""Load the curated archive from catalog/fixtures/collections.json.

Idempotent: upserts on `youtube_id`. Asks for confirmation before writing, and
prints the database path and settings module in the prompt.
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Collection, CustomaryRegion, Format, Video, VideoFormat

FIXTURE = Path(__file__).resolve().parent.parent.parent / "fixtures" / "collections.json"

# Seeded in full, including terms no current entry uses, so curators pick from
# a list rather than typing a near-miss.
FORMAT_VOCABULARY = [
    "Kompilasi album",
    "Rekaman arsip",
    "Rekaman lagu",
    "Audio saja",
    "Video musik",
    "Video lirik",
    "Lirik terjemahan",
    "Versi cover",
    "Karaoke",
    "Paduan suara",
    "Pertunjukan langsung",
]

REQUIRED_FIELDS = (
    "slug",
    "title",
    "artist",
    "youtubeId",
    "region",
    "customaryRegion",
    "language",
    "formats",
    "note",
    "description",
    "context",
)


class Command(BaseCommand):
    help = (
        "Seed collections, vocabulary, and videos from "
        "catalog/fixtures/collections.json"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Skip the confirmation prompt. For CI and scripted deploys.",
        )
        parser.add_argument(
            "--file",
            dest="path",
            default=str(FIXTURE),
            help="Read from a different JSON file.",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Berkas seed tidak ditemukan: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"JSON tidak valid di {path}: {exc}") from exc

        self._validate(payload)

        video_count = sum(len(collection["videos"]) for collection in payload)

        if options["interactive"] and not self._confirm(path, payload, video_count):
            self.stdout.write(self.style.WARNING("Dibatalkan. Tidak ada data yang ditulis."))
            return

        with transaction.atomic():
            stats = self._seed(payload)

        self.stdout.write(
            self.style.SUCCESS(
                "Selesai. "
                f"Koleksi: {stats['collections_created']} baru / "
                f"{stats['collections_updated']} diperbarui. "
                f"Video: {stats['videos_created']} baru / "
                f"{stats['videos_updated']} diperbarui."
            )
        )

    # -- validation ---------------------------------------------------------

    def _validate(self, payload) -> None:
        """Check the whole payload before any of it is written."""

        if not isinstance(payload, list) or not payload:
            raise CommandError("Berkas seed harus berupa array koleksi yang tidak kosong.")

        errors: list[str] = []
        seen_youtube_ids: dict[str, str] = {}
        seen_slugs: set[str] = set()
        valid_regions = set(CustomaryRegion.values)

        for collection in payload:
            for key in ("id", "title", "videos"):
                if key not in collection:
                    errors.append(f"Koleksi kehilangan field '{key}'.")

            for video in collection.get("videos", []):
                label = video.get("slug") or video.get("title") or "<tanpa slug>"

                for field in REQUIRED_FIELDS:
                    if not video.get(field):
                        errors.append(f"{label}: field '{field}' kosong atau tidak ada.")

                youtube_id = video.get("youtubeId")
                if youtube_id:
                    if youtube_id in seen_youtube_ids:
                        errors.append(
                            f"{label}: youtubeId '{youtube_id}' dipakai juga oleh "
                            f"'{seen_youtube_ids[youtube_id]}'. Satu URL YouTube = satu entri."
                        )
                    seen_youtube_ids[youtube_id] = label

                slug = video.get("slug")
                if slug:
                    if slug in seen_slugs:
                        errors.append(f"{label}: slug '{slug}' duplikat.")
                    seen_slugs.add(slug)

                region = video.get("customaryRegion")
                if region and region not in valid_regions:
                    errors.append(
                        f"{label}: wilayah adat '{region}' tidak dikenal. "
                        f"Pilih salah satu dari: {', '.join(sorted(valid_regions))}."
                    )

                for fmt in video.get("formats", []):
                    if fmt not in FORMAT_VOCABULARY:
                        errors.append(
                            f"{label}: bentuk video '{fmt}' di luar kosakata. "
                            f"Gunakan: {', '.join(FORMAT_VOCABULARY)}."
                        )

        if errors:
            listed = "\n  - ".join(errors[:20])
            more = f"\n  … dan {len(errors) - 20} lagi." if len(errors) > 20 else ""
            raise CommandError(f"Data seed tidak lolos validasi:\n  - {listed}{more}")

    # -- confirmation -------------------------------------------------------

    def _confirm(self, path: Path, payload, video_count: int) -> bool:
        from django.conf import settings

        database = settings.DATABASES["default"]["NAME"]
        existing_collections = Collection.objects.count()
        existing_videos = Video.objects.count()

        if existing_videos or existing_collections:
            state = (
                f"{existing_collections} koleksi, {existing_videos} video sudah ada "
                "→ akan di-update (upsert)"
            )
        else:
            state = "database masih kosong → semua akan dibuat baru"

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Seed data kastaumuzik"))
        self.stdout.write(f"  Database : {database}")
        self.stdout.write(f"  Settings : {settings.SETTINGS_MODULE}")
        self.stdout.write(f"  Sumber   : {path}")
        self.stdout.write(f"  Isi      : {len(payload)} koleksi, {video_count} video")
        self.stdout.write(f"  Saat ini : {state}")
        self.stdout.write("")

        if not settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    "  DEBUG=False — ini kemungkinan besar database produksi."
                )
            )
            self.stdout.write("")

        answer = input("Lanjutkan? [y/N]: ").strip().lower()
        return answer in ("y", "yes")

    # -- writing ------------------------------------------------------------

    def _seed(self, payload) -> dict[str, int]:
        formats = {
            name: Format.objects.get_or_create(name=name)[0] for name in FORMAT_VOCABULARY
        }

        stats = dict.fromkeys(
            ("collections_created", "collections_updated", "videos_created", "videos_updated"), 0
        )

        for index, entry in enumerate(payload):
            collection, created = Collection.objects.update_or_create(
                slug=entry["id"],
                defaults={"title": entry["title"], "order": index},
            )
            stats["collections_created" if created else "collections_updated"] += 1

            for position, video_data in enumerate(entry["videos"]):
                video, created = Video.objects.update_or_create(
                    youtube_id=video_data["youtubeId"],
                    defaults={
                        "slug": video_data["slug"],
                        "title": video_data["title"],
                        "artist": video_data["artist"],
                        "collection": collection,
                        "region": video_data["region"],
                        "customary_region": video_data["customaryRegion"],
                        "language": video_data["language"],
                        "year": video_data.get("year", ""),
                        "duration": video_data.get("duration", ""),
                        "position": position,
                        "note": video_data["note"],
                        "description": video_data["description"],
                        "context": video_data["context"],
                        "is_published": True,
                    },
                )
                # Rewritten wholesale: the list order is the payload.
                video.video_formats.all().delete()
                VideoFormat.objects.bulk_create(
                    VideoFormat(video=video, format=formats[name], position=order)
                    for order, name in enumerate(video_data["formats"])
                )
                stats["videos_created" if created else "videos_updated"] += 1

        return stats

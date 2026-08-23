"""Where curators review what the public sent in."""

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.text import slugify
from unfold.admin import ModelAdmin

from catalog.models import Collection, CustomaryRegion, Video

from .models import Submission, SubmissionStatus

# Placeholder for what an accepted submission cannot tell us.
UNCONFIRMED = "Belum dipastikan"


@admin.register(Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = ["title", "performer", "status", "created_at", "reviewed_by"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "performer", "description", "youtube_url"]
    date_hierarchy = "created_at"
    actions = ["mark_in_review", "accept_submissions", "reject_submissions"]
    list_per_page = 50

    readonly_fields = [
        "youtube_url",
        "youtube_id",
        "title",
        "performer",
        "description",
        "created_at",
        "updated_at",
        "reviewed_by",
        "reviewed_at",
        "submitted_from",
    ]

    fieldsets = (
        (
            "Usulan",
            {
                "fields": (
                    "title",
                    "performer",
                    "youtube_url",
                    "youtube_id",
                    "description",
                ),
                "description": "Dikirim publik lewat /usulkan/. Isinya tidak dapat diubah.",
            },
        ),
        ("Tinjauan", {"fields": ("status", "curator_note")}),
        (
            "Jejak",
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                    "created_at",
                    "updated_at",
                    "submitted_from",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request) -> bool:
        # Submissions only ever arrive through the public form.
        return False

    @admin.action(description="Tandai sedang ditinjau")
    def mark_in_review(self, request, queryset):
        updated = queryset.update(
            status=SubmissionStatus.IN_REVIEW,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} usulan ditandai sedang ditinjau.")

    @admin.action(description="Terima dan buat draft video")
    def accept_submissions(self, request, queryset):
        collection = Collection.objects.order_by("order").first()
        if collection is None:
            self.message_user(
                request,
                "Belum ada koleksi. Buat minimal satu kategori sebelum menerima usulan.",
                level=messages.ERROR,
            )
            return

        created, skipped = 0, []

        for submission in queryset:
            if not submission.youtube_id:
                skipped.append(f"{submission.title} (tautan tidak terbaca)")
                continue
            if Video.objects.filter(youtube_id=submission.youtube_id).exists():
                skipped.append(f"{submission.title} (sudah ada di arsip)")
                continue

            Video.objects.create(
                slug=self._unique_slug(submission),
                title=submission.title,
                artist=submission.performer,
                youtube_id=submission.youtube_id,
                channel=UNCONFIRMED,
                collection=collection,
                region=UNCONFIRMED,
                customary_region=CustomaryRegion.UNCONFIRMED,
                language=UNCONFIRMED,
                language_group=UNCONFIRMED,
                note=submission.description[:300],
                description=submission.description,
                context=(
                    "Dibuat dari usulan publik. Kredit, bahasa, wilayah adat, dan "
                    "kategori masih perlu diperiksa kurator terhadap sumber aslinya."
                ),
                is_published=False,
            )
            submission.status = SubmissionStatus.ACCEPTED
            submission.reviewed_by = request.user
            submission.reviewed_at = timezone.now()
            submission.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
            created += 1

        if created:
            self.message_user(
                request,
                f"{created} draft video dibuat, belum terbit. Lengkapi metadata dan "
                f"tentukan kategorinya — sementara semuanya masuk “{collection.title}” "
                "dan ditandai “Belum dipastikan”.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                "Dilewati: " + "; ".join(skipped),
                level=messages.WARNING,
            )

    @admin.action(description="Tolak usulan")
    def reject_submissions(self, request, queryset):
        # The note has to exist before the status can change.
        missing = [s.title for s in queryset if not s.curator_note.strip()]
        if missing:
            self.message_user(
                request,
                "Isi dulu catatan kurator sebagai alasan penolakan untuk: "
                + ", ".join(missing),
                level=messages.ERROR,
            )
            return

        updated = queryset.update(
            status=SubmissionStatus.REJECTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} usulan ditolak.")

    @staticmethod
    def _unique_slug(submission) -> str:
        base = slugify(f"{submission.title}-{submission.performer}")[:110] or "usulan"
        slug = base
        suffix = 2
        while Video.objects.filter(slug=slug).exists():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

"""Recordings the public sends in for curator review."""

from django.conf import settings
from django.db import models


class SubmissionStatus(models.TextChoices):
    NEW = "NEW", "Baru"
    IN_REVIEW = "IN_REVIEW", "Sedang ditinjau"
    ACCEPTED = "ACCEPTED", "Diterima"
    REJECTED = "REJECTED", "Ditolak"


class Submission(models.Model):
    """One submitted YouTube link, awaiting a curator's judgement."""

    youtube_url = models.URLField("tautan YouTube", max_length=300)
    youtube_id = models.CharField(
        "ID YouTube",
        max_length=20,
        blank=True,
        help_text="Diambil dari tautan saat disimpan; dipakai untuk mendeteksi duplikat.",
    )
    title = models.CharField("judul", max_length=200)
    performer = models.CharField(
        "artis atau pelaku", max_length=200, help_text="Artis, grup, atau koor."
    )
    description = models.TextField(
        "deskripsi", help_text="Konteks, asal, atau makna lagu yang diketahui."
    )

    status = models.CharField(
        "status",
        max_length=12,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NEW,
    )
    curator_note = models.TextField(
        "catatan kurator",
        blank=True,
        help_text="Alasan penolakan, atau catatan tinjauan. Wajib saat menolak.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ditinjau oleh",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_submissions",
    )
    reviewed_at = models.DateTimeField("waktu tinjauan", null=True, blank=True)

    # For rate-limit forensics; never exposed through the API.
    submitted_from = models.GenericIPAddressField("dikirim dari", null=True, blank=True)

    created_at = models.DateTimeField("dibuat", auto_now_add=True)
    updated_at = models.DateTimeField("diperbarui", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "usulan"
        verbose_name_plural = "usulan"
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.title} — {self.performer}"

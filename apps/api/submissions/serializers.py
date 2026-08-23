"""Write serializer for public submissions.

The client-side checks in `usulkan.astro` are for feedback; these decide.
"""

from rest_framework import serializers

from catalog.models import Video

from .models import Submission, SubmissionStatus
from .youtube import extract_youtube_id


class SubmissionSerializer(serializers.ModelSerializer):
    # Honeypot: hidden from people, handled in the view rather than raising.
    website = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Biarkan kosong.",
    )

    class Meta:
        model = Submission
        fields = ["youtube_url", "title", "performer", "description", "website"]
        extra_kwargs = {
            "description": {"min_length": 20},
        }

    def validate_youtube_url(self, value: str) -> str:
        youtube_id = extract_youtube_id(value)
        if youtube_id is None:
            raise serializers.ValidationError("Masukkan tautan video YouTube yang valid.")

        if Video.objects.filter(youtube_id=youtube_id).exists():
            raise serializers.ValidationError(
                "Video ini sudah ada di arsip kastaumuzik."
            )

        # A previously rejected link may be sent again.
        already_queued = (
            Submission.objects.filter(youtube_id=youtube_id)
            .exclude(status=SubmissionStatus.REJECTED)
            .exists()
        )
        if already_queued:
            raise serializers.ValidationError(
                "Video ini sudah pernah diusulkan dan sedang menunggu tinjauan."
            )

        return value

    def create(self, validated_data):
        validated_data.pop("website", None)
        validated_data["youtube_id"] = extract_youtube_id(validated_data["youtube_url"]) or ""
        return super().create(validated_data)

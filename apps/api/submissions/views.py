"""The one write endpoint on the API.

`CreateModelMixin` only, so there is no list or detail route and
`GET /api/v1/submissions/` is a 405. Guarded by per-IP throttling, a honeypot
field, and server-side validation of the link.
"""

import logging

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from .models import Submission
from .serializers import SubmissionSerializer
from .throttles import SubmissionDailyThrottle, SubmissionHourlyThrottle

logger = logging.getLogger(__name__)


class SubmissionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Accepts one submitted recording for curator review."""

    queryset = Submission.objects.none()
    serializer_class = SubmissionSerializer
    throttle_classes = [SubmissionHourlyThrottle, SubmissionDailyThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Answered with the same 201 a real submission gets.
        if serializer.validated_data.get("website"):
            logger.info("Honeypot tripped from %s", self._client_ip(request))
            return Response(
                {"detail": "Terima kasih. Usulan kamu akan ditinjau kurator."},
                status=status.HTTP_201_CREATED,
            )

        serializer.save(submitted_from=self._client_ip(request))

        return Response(
            {"detail": "Terima kasih. Usulan kamu akan ditinjau kurator."},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _client_ip(request) -> str | None:
        """The submitter's address as seen through the reverse proxy."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

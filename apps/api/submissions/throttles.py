"""Per-IP limits on the submission endpoint.

Two windows, hourly and daily. `ScopedRateThrottle` handles one scope per view,
so each window is its own class. Rates come from the environment.
"""

from rest_framework.throttling import SimpleRateThrottle


class _SubmissionThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        # Keyed on the address the proxy reports.
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ident = (
            forwarded.split(",")[0].strip()
            if forwarded
            else request.META.get("REMOTE_ADDR")
        )
        return self.cache_format % {"scope": self.scope, "ident": ident}


class SubmissionHourlyThrottle(_SubmissionThrottle):
    scope = "submission-hour"


class SubmissionDailyThrottle(_SubmissionThrottle):
    scope = "submission-day"

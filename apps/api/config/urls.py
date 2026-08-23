"""URL routing."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from catalog.views import CollectionViewSet, VideoViewSet
from submissions.views import SubmissionViewSet

router = DefaultRouter()
router.register("collections", CollectionViewSet, basename="collection")
router.register("videos", VideoViewSet, basename="video")
# CreateModelMixin only, so no list or detail URL is generated.
router.register("submissions", SubmissionViewSet, basename="submission")

ADMIN_PATH = "site-manager/"

urlpatterns = [
    path("", RedirectView.as_view(url=f"/{ADMIN_PATH}", permanent=False)),
    path(ADMIN_PATH, admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

"""The curated archive.

Field names are English; the values curators enter stay Indonesian and render
straight onto the site.
"""

from django.db import models


class CustomaryRegion(models.TextChoices):
    """The seven customary regions of Tanah Papua, plus honest placeholders."""

    MAMTA = "Mamta", "Mamta"
    SAIRERI = "Saireri", "Saireri"
    DOMBERAI = "Domberai", "Domberai"
    BOMBERAI = "Bomberai", "Bomberai"
    HA_ANIM = "Ha Anim", "Ha Anim"
    LA_PAGO = "La Pago", "La Pago"
    MEE_PAGO = "Mee Pago", "Mee Pago"
    CROSS_REGION = "Lintas wilayah adat", "Lintas wilayah adat"
    UNCONFIRMED = "Belum dipastikan", "Belum dipastikan"


class Collection(models.Model):
    """A shelf, and the archive's only statement about what kind of music this is.

    There is no separate genre model; the collection carries that meaning.
    """

    slug = models.SlugField("slug", max_length=80, unique=True)
    title = models.CharField("judul", max_length=120)
    order = models.PositiveSmallIntegerField(
        "urutan",
        default=0,
        help_text="Urutan tampil, dari pintu masuk paling luas ke paling khusus.",
    )

    class Meta:
        ordering = ["order", "slug"]
        verbose_name = "koleksi"
        verbose_name_plural = "koleksi"

    def __str__(self) -> str:
        return self.title


class Format(models.Model):
    """How the recording is presented. A controlled vocabulary, not free text."""

    name = models.CharField("nama", max_length=60, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "bentuk video"
        verbose_name_plural = "bentuk video"

    def __str__(self) -> str:
        return self.name


class PublishedVideoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Video(models.Model):
    """One catalogue entry, which is one source video.

    Chapters inside a compilation are never separate entries; a compilation is
    stored whole.
    """

    slug = models.SlugField("slug", max_length=120, unique=True)
    title = models.CharField("judul", max_length=200)
    artist = models.CharField("artis", max_length=200)
    youtube_id = models.CharField(
        "ID YouTube",
        max_length=20,
        unique=True,
        help_text="Satu URL YouTube harus menjadi satu entri.",
    )

    collection = models.ForeignKey(
        Collection,
        verbose_name="koleksi",
        on_delete=models.PROTECT,
        related_name="videos",
        help_text="Tepat satu kategori Jelajah.",
    )

    region = models.CharField("daerah", max_length=120, help_text="Kabupaten atau kota.")
    customary_region = models.CharField(
        "wilayah adat",
        max_length=40,
        choices=CustomaryRegion.choices,
        default=CustomaryRegion.UNCONFIRMED,
    )
    language = models.CharField("bahasa", max_length=120)

    # Ordered through VideoFormat: the first format is the label on the video
    # card. A plain ManyToMany would return them alphabetically.
    formats = models.ManyToManyField(
        Format,
        through="VideoFormat",
        related_name="videos",
        verbose_name="bentuk video",
    )

    year = models.CharField("tahun", max_length=10, blank=True)
    duration = models.CharField("durasi", max_length=12, blank=True)

    note = models.CharField(
        "catatan singkat",
        max_length=300,
        help_text="Satu kalimat; dipakai sebagai meta description.",
    )
    description = models.TextField("deskripsi")
    context = models.TextField(
        "konteks",
        help_text="Asal sumbernya, dan apa yang masih belum pasti.",
    )

    is_featured = models.BooleanField(
        "pilihan kurator",
        default=False,
        help_text="Tampil di baris pilihan kurator pada halaman Jelajah.",
    )

    position = models.PositiveSmallIntegerField(
        "urutan",
        default=0,
        help_text="Urutan tampil di dalam kategorinya.",
    )

    is_published = models.BooleanField(
        "terbit",
        default=True,
        help_text="Draft hasil usulan mulai dari tidak tercentang.",
    )

    created_at = models.DateTimeField("dibuat", auto_now_add=True)
    updated_at = models.DateTimeField("diperbarui", auto_now=True)

    objects = models.Manager()
    published = PublishedVideoManager()

    class Meta:
        ordering = ["position", "title"]
        verbose_name = "video"
        verbose_name_plural = "video"
        indexes = [
            models.Index(fields=["is_published"]),
            models.Index(fields=["position", "title"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} — {self.artist}"

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def ordered_formats(self) -> list[str]:
        """Formats in curator order, read from the prefetched join rows."""
        return [link.format.name for link in self.video_formats.all()]


class VideoFormat(models.Model):
    """Join row that remembers where a format sits in a video's list."""

    video = models.ForeignKey(
        Video,
        verbose_name="video",
        on_delete=models.CASCADE,
        related_name="video_formats",
    )
    format = models.ForeignKey(
        Format,
        verbose_name="bentuk video",
        on_delete=models.CASCADE,
        related_name="video_links",
    )
    position = models.PositiveSmallIntegerField(
        "urutan",
        default=0,
        help_text="Yang pertama tampil sebagai label di kartu video.",
    )

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["video", "format"], name="unique_video_format"),
        ]
        verbose_name = "bentuk video pada video"
        verbose_name_plural = "bentuk video pada video"

    def __str__(self) -> str:
        return f"{self.video.title} — {self.format.name}"

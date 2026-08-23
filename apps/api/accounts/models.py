from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Creates users identified by email rather than username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Alamat email wajib diisi.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser harus punya is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser harus punya is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """A curator or an administrator, identified by email.

    Roles are groups, not fields. The ``Curator`` group and its permissions are
    created in `accounts/migrations/0002_curator_group.py`.
    """

    username = None
    email = models.EmailField("email", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta(AbstractUser.Meta):
        verbose_name = "pengguna"
        verbose_name_plural = "pengguna"

    def __str__(self) -> str:
        return self.email

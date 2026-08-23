"""User admin, rendered through Unfold so it matches the rest of the site."""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User

# Re-registered below under Unfold's ModelAdmin.
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ["email", "first_name", "last_name", "is_staff", "role_names"]
    list_filter = ["is_staff", "is_superuser", "is_active", "groups"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]

    readonly_fields = ["last_login", "date_joined"]

    # Django's defaults are organised around `username`, which this model
    # does not have.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identitas", {"fields": ("first_name", "last_name")}),
        (
            "Hak akses",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "description": (
                    "Kurator cukup dicentang “staf” dan dimasukkan ke grup Curator. "
                    "Hak per-model diatur lewat grup, bukan satu per satu."
                ),
            },
        ),
        ("Jejak", {"fields": ("last_login", "date_joined"), "classes": ("collapse",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )

    filter_horizontal = ["groups", "user_permissions"]

    @admin.display(description="peran")
    def role_names(self, obj) -> str:
        groups = ", ".join(group.name for group in obj.groups.all())
        if obj.is_superuser:
            return f"Superuser{', ' + groups if groups else ''}"
        return groups or "—"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups")

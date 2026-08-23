"""Create the Curator group and its permissions.

A curator is a staff user in this group: view, add, and change catalogue
records, and review submissions. No delete, and no user management.
"""

from django.db import migrations

CURATOR_GROUP = "Curator"

# (app_label, model, [actions])
CURATOR_PERMISSIONS = [
    ("catalog", "video", ["view", "add", "change"]),
    ("catalog", "collection", ["view", "add", "change"]),
    ("catalog", "format", ["view", "add", "change"]),
    # No "add": submissions arrive from the public form.
    ("submissions", "submission", ["view", "change"]),
]


def create_curator_group(apps, schema_editor):
    from django.contrib.auth.management import create_permissions

    # post_migrate has not fired yet during this run, so the permission table
    # would be empty on a fresh database.
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    group, _ = Group.objects.get_or_create(name=CURATOR_GROUP)

    wanted = []
    for app_label, model, actions in CURATOR_PERMISSIONS:
        for action in actions:
            wanted.append(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    content_type__model=model,
                    codename=f"{action}_{model}",
                )
            )

    group.permissions.set(wanted)


def delete_curator_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=CURATOR_GROUP).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("catalog", "0001_initial"),
        ("submissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_curator_group, delete_curator_group),
    ]

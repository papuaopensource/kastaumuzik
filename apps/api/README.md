# api

Curation admin and read API. Django 6 with SQLite, dependencies managed by `uv`.

## Run it

```bash
uv sync
cp .env.example .env
# then put a SECRET_KEY in .env:
uv run python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

pnpm --filter api migrate
pnpm --filter api seed          # asks for confirmation before writing
uv run python manage.py createsuperuser   # asks for an email, not a username
pnpm --filter api dev           # http://localhost:8000
```

- Admin: <http://localhost:8000/site-manager/> — `/` redirects there

## Endpoints

Everything under `/api/v1/`, public in this phase.

| Endpoint | Method |
| --- | --- |
| `/api/v1/collections/` | GET |
| `/api/v1/videos/`, `/api/v1/videos/<slug>/` | GET |
| `/api/v1/submissions/` | POST |

Read-only and write-only come from which mixins the viewsets inherit, so there is no unguarded route to forget: `GET /api/v1/submissions/` is a 405.

The write endpoint is guarded by per-IP throttling in two windows, a honeypot field answered with a normal 201, and server-side validation of the YouTube link.

## What to know

- **Two roles.** Superuser, and `Curator` — a group created by a data migration, so a fresh database matches the server. Curators may add and change catalogue records and review submissions; they may not delete a video or touch user accounts.
- **Settings are split** into `config/settings/{base,development,production}.py`. Secrets come from the environment through python-decouple.
- **Production keeps SQLite**, with the PRAGMAs recommended by [dj-lite](https://github.com/adamghill/dj-lite) and a file-based cache for throttle counters (the in-memory default is per-process and would multiply every rate limit by the worker count).
- **Formats are ordered**, through a join model. The first one is the label shown on a video card.
- **There is no genre model.** The collection a recording sits in is the archive's statement about what kind of music it is.
- **Accounts are identified by email**; `username` is removed, so the admin login asks for an email and a password.

## Apps

```
accounts/      custom User, Curator group migration
catalog/       Collection, Format, Video, related-video scoring
submissions/   what the public sends in through /usulkan/
```

Data model details, the seeding command, and the metadata vocabulary are in [DEVELOPMENT.md](../../DEVELOPMENT.md).

# Development guide

Technical notes for kastaumuzik. For an overview of the project, see [README.md](./README.md).

## Layout

```
kastaumuzik/
├── turbo.json, pnpm-workspace.yaml
├── apps/
│   ├── web/        Astro site → Cloudflare Workers
│   └── api/        Django admin + read API → VPS
```

`apps/web` is a pnpm workspace package; `apps/api` has a thin `package.json` whose scripts shell out to `uv`, so turbo can drive both with one command.

## Running locally

Requires Node.js 20+, [pnpm](https://pnpm.io), and [uv](https://docs.astral.sh/uv/).

```bash
pnpm install                       # web dependencies
uv sync --directory apps/api       # api dependencies

cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
# generate a SECRET_KEY for apps/api/.env:
uv run --directory apps/api python -c \
  "from django.core.management.utils import get_random_secret_key as k; print(k())"

pnpm --filter api migrate
pnpm --filter api seed             # asks for confirmation before writing
pnpm --filter api exec uv run python manage.py createsuperuser   # asks for an email
```

Then run both:

```bash
pnpm dev            # turbo runs the Astro dev server and Django together
```

- Site: <http://localhost:4321>
- Admin: <http://localhost:8000/site-manager/> (`/` redirects there)
- API docs: <http://localhost:8000/api/docs/>

The build does not touch the API — only three pages are prerendered, and none of them read the catalogue. The API has to be running to *view* the catalogue pages, not to build them.

Astro keeps its dev server alive across runs. After changing dependencies or config, run `pnpm --filter web exec astro dev stop` before `pnpm dev`.

## apps/api

Django 6.1, SQLite, `uv` for dependencies. Settings are split:

| Module | Used by |
| --- | --- |
| `config/settings/base.py` | shared; reads everything secret through python-decouple |
| `config/settings/development.py` | the default for `manage.py` |
| `config/settings/production.py` | set `DJANGO_SETTINGS_MODULE` to select it |

Production keeps SQLite and applies the PRAGMAs from [dj-lite](https://github.com/adamghill/dj-lite) — WAL, `synchronous=NORMAL`, `transaction_mode=IMMEDIATE`, and a busy timeout. Django 6 supports `init_command` and `transaction_mode` natively, so no extra package is involved. Throttle counters go to a **file-based cache**, not the in-memory default, because the default is per-process and would silently multiply every rate limit by the worker count.

### Apps

- **`accounts`** — a custom `User` identified by **email**; `username` is removed. Roles are groups, not fields.
- **`catalog`** — `Collection`, `Format`, `Video`, and the join model that keeps formats **in order**. That order matters: the first format is the label on the video card.
  There is no genre model. A recording's musical character is already why it sits on one collection rather than another, and keeping both made curators classify the same thing twice with two vocabularies free to disagree.
- **`submissions`** — `Submission`, what the public sends in through `/usulkan/`.

### Roles

`Curator` is created by a data migration in `accounts/migrations/0002_curator_group.py`, so a fresh database comes up with the same permissions as the server. A curator may view/add/change catalogue records and review submissions. They may **not** delete a video or touch user accounts.

### API

Everything under `/api/v1/`, public in this phase.

| Endpoint | Method |
| --- | --- |
| `/api/v1/collections/` | GET |
| `/api/v1/videos/`, `/api/v1/videos/<slug>/` | GET |
| `/api/v1/submissions/` | POST |

Read-only and write-only are enforced by **which mixins the viewsets inherit**, not by checking `request.method`. There is no list route for submissions to forget to guard: `GET /api/v1/submissions/` is a 405.

With no API key in front of it, three things guard the write endpoint: per-IP throttling in two windows (hour and day, both from env), a honeypot field answered with a normal 201 so a bot learns nothing, and server-side validation of the YouTube link.

### Seeding

`pnpm --filter api seed` loads `apps/api/catalog/fixtures/collections.json`. It prints the database path and settings module and asks before writing, because the realistic mistake is seeding while pointed at production. `--noinput` skips the prompt for CI. It upserts on `youtube_id`, so running it twice changes nothing.

It also validates the data against the vocabulary below and refuses anything outside it.

## Adding a recording

Through the admin at `/site-manager/`, or by adding to the fixture and reseeding. Fields mirror the old JSON:

- **Customary region** — one of `Mamta`, `Saireri`, `Domberai`, `Bomberai`, `Ha Anim`, `La Pago`, `Mee Pago`. Use `Belum dipastikan` when the source does not say, and `Lintas wilayah adat` for compilations.
- **Koleksi** — `Arsip musik Papua` · `Lagu daerah` · `Pop & rock Papua` · `Lagu rohani`. This is the archive's only statement about what kind of music a recording is.
- **Bentuk video** — `Kompilasi album` · `Rekaman arsip` · `Rekaman lagu` · `Audio saja` · `Video musik` · `Video lirik` · `Lirik terjemahan` · `Versi cover` · `Karaoke` · `Paduan suara` · `Pertunjukan langsung`. The **first** one is the label shown on the card.
- **Uncertainty** is written as it is: `Belum dipastikan` for the region, and the reason in `context`.

Pull the title, year, and duration from YouTube rather than estimating:

```bash
curl -s "https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json"
```

One YouTube URL is one entry — `youtube_id` is unique in the database. Do not split a compilation into chapters. A video belongs to exactly one collection; the foreign key enforces it.

Values stay in Indonesian: they render straight onto the site.

> `curationStatus` is documented here historically but exists on no entry and in no model. It was dropped rather than invented; say so if you want it back.

## apps/web

### Where the data comes from

`src/lib/catalog.ts` fetches the archive and maps the API's snake_case onto the camelCase the templates use. `src/lib/collections.ts` wraps it in `getCatalog()`.

The catalogue pages are **rendered on demand**, so a video published in the admin is on the site immediately, with no rebuild. `index`, `jelajah`, `riwayat`, and `video/[slug]` all carry `export const prerender = false`; `tentang`, `pernyataan`, `usulkan`, `404`, and `500` stay static.

`getCatalog()` is **not memoised**. Module state in a Worker lives as long as the isolate, so caching the catalogue there would serve a stale archive for minutes or hours after a publish.

The trade-off is deliberate: the API is now a hard dependency of every catalogue page. When it is unreachable those pages return 500 and render `src/pages/500.astro`, which is prerendered so it does not need the API itself. The static pages keep working.

`API_ORIGIN` has no `PUBLIC_` prefix, so it never reaches the client bundle.

### Cloudflare Workers

`wrangler.jsonc` is deliberately minimal; the Astro adapter supplies the entrypoint. Static files come from `dist/client`.

`API_ORIGIN` is read from the Worker's environment via `cloudflare:workers` (`Astro.locals.runtime.env` was removed in Astro 6), so the API can move without redeploying the site. `.env` is the local fallback.

```bash
pnpm --filter web build
pnpm --filter web exec wrangler dev     # local Worker, including the POST route
pnpm --filter web deploy
```

### Alpine

Alpine handles behaviour on top of markup Astro already rendered — `x-show`, `x-model`, `@click`, ordering. It never renders the catalogue: `x-for` over videos would empty the page for anyone without JavaScript and for crawlers.

| Component | Page |
| --- | --- |
| `homeFeed` | shuffle, chips, endless scroll |
| `explore` | ranked search, URL sync, "continue watching" |
| `watchHistory` | the history page |
| `submissionForm` | submit, draft, error states |
| `watchPage` | share menu, records the view |

`Alpine.store("history")` owns `kastaumuzik:watch-history` — one description of that key instead of the two copies that used to live in `[slug].astro` and `riwayat.astro`.

**The theme script in `BaseHead.astro` stays inline vanilla.** It runs before first paint, long before Alpine parses; moving it would make the page flash the wrong theme. Hand-written dark rules use `[data-theme="dark"] .your-class`, outside Tailwind's variant system.

### Ranking

- **Related videos** are scored in Django (`catalog/recommendations.py`) — language 4, customary region 3, format ×1 — and shipped as a field on the list response, so the build stays one request. Regions that mean "unknown" are excluded from matching, read off the `CustomaryRegion` enum rather than restated as literals.
- **Curator picks** come from `is_featured`, not analytics, and appear on `/jelajah/`. Their order is the shelf order curators already control through `position`.
- **Search** scores each field separately (title > artist > facets), so the obvious answer ranks first instead of everything matching equally.
- **Home is pure chance.** Every recording gets the same shot at being seen, and no visitor is funnelled back to what they already watched.

### Styling

Tailwind v4 as a Vite plugin; everything lives in `src/styles/global.css`, no config file. **Renamed in v4** and silently dead under the old names: `shadow-sm` → `shadow-xs`, `shadow` → `shadow-sm`, `rounded` → `rounded-sm`, `ring` → `ring-3`, `bg-gradient-to-*` → `bg-linear-to-*`.

## Checks

```bash
pnpm check                                  # astro check + django check
pnpm --filter api exec uv run ruff check .
pnpm build                                  # both apps; API must be live
```

There is no automated test suite yet — the behaviour above was verified by hand.

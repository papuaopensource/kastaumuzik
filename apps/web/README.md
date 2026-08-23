# web

The public site. Astro on Cloudflare Workers, catalogue pages rendered on demand.

## Run it

```bash
cp .env.example .env
pnpm --filter web dev          # http://localhost:4321
```

The API must be running to view the catalogue pages. The build itself does not need it.

```bash
pnpm --filter web build
pnpm --filter web exec wrangler dev    # local Worker, including the POST route
pnpm --filter web deploy
```

## What to know

- **The catalogue is read on every request**, so a video published in the admin appears at once with no rebuild. `index`, `jelajah`, `riwayat`, and `video/[slug]` are on-demand; `tentang`, `pernyataan`, `usulkan`, `404`, and `500` are static.
- **The API is a hard dependency of those pages.** If it is unreachable they return 500 and render the prerendered `500.astro`.
- **`src/pages/api/submissions.ts`** forwards a submitted recording to Django, so the browser posts to its own origin.
- **`API_ORIGIN` has no `PUBLIC_` prefix**, so it never reaches the client bundle.
- **Alpine adds behaviour to server-rendered markup** — it never renders the video list, which would empty the page for anyone without JavaScript.

## Layout

```
src/
├── lib/catalog.ts       reads the API, maps snake_case → camelCase
├── lib/collections.ts   getCatalog(), one read per request
├── alpine/              one file per interactive component
├── components/, layouts/, pages/
└── styles/global.css    Tailwind v4 entry and theme
```

Architecture notes, the Alpine component list, and the ranking rules are in [DEVELOPMENT.md](../../DEVELOPMENT.md).

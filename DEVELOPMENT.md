# Development guide

Technical notes for KastauMuzik. For an overview of the project, see [README.md](./README.md).

## Running locally

Requires Node.js 20+ and [pnpm](https://pnpm.io).

```bash
pnpm install
pnpm dev        # dev server at http://localhost:4321
pnpm build      # runs astro check, then a static build into dist/
pnpm preview    # preview the build output
```

Astro keeps the dev server alive across runs. After changing dependencies or config, run `pnpm astro dev stop` before `pnpm dev`, otherwise a stale process serves the old runtime.

## Structure

```
src/
├── data/collections.json     # the single source of collection content
├── lib/collections.ts        # shelf order, facets, filters, search text
├── types/index.d.ts
├── styles/global.css         # Tailwind entry and theme config
├── components/
├── layouts/Layout.astro
└── pages/
    ├── index.astro, jelajah.astro, tentang.astro, pernyataan.astro
    └── koleksi/[slug].astro  # one page per slug in collections.json
```

Pages read `src/lib/collections.ts`, never the JSON directly. Adding a recording updates counts, category tiles, filters, and routes on its own.

Shelf order comes from `shelfOrder` in `src/lib/collections.ts`, not the order in the JSON.

## Adding a recording

Add an object to the `videos` array of one shelf in [`src/data/collections.json`](src/data/collections.json):

```jsonc
{
  "slug": "awak-param-melani-sawaki",   // unique; becomes /koleksi/<slug>/
  "title": "Awak Param",
  "artist": "Melani Sawaki",
  "youtubeId": "5Lr68uxQS0o",
  "startSeconds": 8,                    // optional, for a chapter in a compilation
  "endSeconds": 171,                    // optional
  "channel": "Geen Roger Ps",
  "region": "Biak",                     // regency or city
  "customaryRegion": "Saireri",
  "language": "Biak",
  "languageGroup": "Biak",              // used as the language category
  "genres": ["Lagu daerah", "Pop Papua"],
  "year": "2021",
  "duration": "4:03",
  "curationStatus": "Kanal warga",      // badge on the card thumbnail
  "note": "One sentence, used as the meta description.",
  "description": "A paragraph about the recording.",
  "context": "Where this came from, and what is still uncertain."
}
```

Pull the title, channel, year, and duration from YouTube rather than estimating:

```bash
curl -s "https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json"
```

Values inside the data stay in Indonesian — they render straight onto the site.

**Customary region** — one of `Mamta`, `Saireri`, `Domberai`, `Bomberai`, `Ha Anim`, `La Pago`, `Mee Pago`. Use `Belum dipastikan` when the source does not say, and `Lintas wilayah adat` for compilations. Categories derive from the data, so an empty region simply does not appear.

**Song type** — reuse the existing terms so categories do not fragment: `Lagu daerah` · `Lagu tarian` · `Lagu rohani` · `Paduan suara` · `Pop Papua` · `Rock Papua` · `Rekaman arsip` · `Arsip Mambesak` · `Rekaman panggung` · `Versi cover` · `Video lirik`.

Four of those feed the filter chips on `/jelajah/` through `modesForVideo` in `src/lib/collections.ts`. Adding a term that belongs to a chip means updating that function too.

**When something is uncertain**, write it as it is: `Belum dipastikan` for the region, `Catatan bahasa terbuka` for `languageGroup`, and the reason in `context`.

## Filter URLs

Filters on `/jelajah/` are mirrored into the URL and can be combined:

```
/jelajah/?q=mambesak&bahasa=Sentani&genre=Lagu+rohani&wilayah=Saireri&mode=arsip
```

Values match the data exactly — `bahasa` is `languageGroup`, `wilayah` is `customaryRegion`, `rak` is the shelf title. Category tiles are plain links, so the page still works without JavaScript.

## Styling and theme

Tailwind v4 runs as a Vite plugin (`@tailwindcss/vite`). There is no `tailwind.config.mjs`; everything is in [`src/styles/global.css`](src/styles/global.css), imported by `Layout.astro`. Custom tokens go in the `@theme` block — `--font-onest` is what makes `font-onest` work.

`dark:` keys off `data-theme` on `<html>`:

- A blocking inline script in `BaseHead.astro` sets it before first paint from `localStorage.theme`, falling back to the system preference. It must stay inline and in `<head>`.
- The footer switch uses Alpine for the click; the active styling is CSS keyed off `data-theme` so it does not flash.
- Hand-written CSS needing a dark variant must use `[data-theme="dark"] .your-class` — those rules sit outside Tailwind's variant system.

**Renamed in v4**, and silently dead under the old names: `shadow-sm` → `shadow-xs`, bare `shadow` → `shadow-sm`, bare `rounded` → `rounded-sm`, bare `ring` → `ring-3`, `bg-gradient-to-*` → `bg-linear-to-*`.

## Client-side JavaScript

Search, filtering, and the shelves are small per-page scripts against the DOM; shelves use CSS `scroll-snap`, not a carousel library. Alpine — registered via [`@astrojs/alpinejs`](https://docs.astro.build/en/guides/integrations-guide/alpinejs/), core only — drives the mobile menu and the theme switch. Elements hidden with `x-show` need `x-cloak`. No third-party CDN requests at runtime; thumbnails come from `i.ytimg.com`.

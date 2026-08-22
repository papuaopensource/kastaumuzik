# Development guide

Technical notes for kastaumuzik. For an overview of the project, see [README.md](./README.md).

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
    ├── index.astro, jelajah.astro, usulkan.astro, tentang.astro, pernyataan.astro
    └── video/[slug].astro    # one page per slug in collections.json
```

Imports use the `@/` alias for anything under `src`, e.g. `import Layout from "@/layouts/Layout.astro"`. It is declared once in `tsconfig.json` under `paths`; Astro picks it up from there, so there is nothing to configure in `astro.config.mjs`.

Pages read `src/lib/collections.ts`, never the JSON directly. Adding a recording updates counts, category tiles, filters, and routes on its own.

Shelf order comes from `shelfOrder` in `src/lib/collections.ts`, not the order in the JSON.

## Adding a recording

Add an object to the `videos` array of one shelf in [`src/data/collections.json`](src/data/collections.json):

```jsonc
{
  "slug": "awak-param-melani-sawaki",   // unique; becomes /video/<slug>/
  "title": "Awak Param",
  "artist": "Melani Sawaki",
  "youtubeId": "5Lr68uxQS0o",
  "channel": "Geen Roger Ps",
  "region": "Biak",                     // regency or city
  "customaryRegion": "Saireri",
  "language": "Biak",
  "languageGroup": "Biak",              // used as the language category
  "genres": ["Lagu daerah", "Pop Papua"], // what kind of music it is
  "formats": ["Rekaman musik"],          // how the source is presented
  "year": "2021",
  "duration": "4:03",
  "curationStatus": "Kredit perlu dilengkapi", // concise editorial status
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

**Jenis musik** — hanya menjelaskan isi musiknya. Gunakan istilah yang sudah ada agar kategori tidak terpecah: `Lagu daerah` · `Lagu tarian` · `Lagu rohani` · `Pop Papua` · `Rock Papua`.

**Bentuk video atau penampilan** — menjelaskan cara sumber disajikan, terpisah dari jenis musik: `Kompilasi album` · `Rekaman arsip` · `Rekaman audio` · `Rekaman musik` · `Video lirik` · `Cover` · `Karaoke` · `Paduan suara` · `Pertunjukan langsung`.

Satu URL YouTube harus menjadi satu entri. Jangan membuat halaman baru dari `startSeconds` atau bab-bab di dalam video kompilasi; simpan kompilasi tersebut sebagai satu video utuh.

**Status kurasi** — gunakan status editorial yang menjelaskan kondisi datanya: `Sumber arsip` · `Kanal artis` · `Kredit perlu dilengkapi` · `Konteks perlu dilengkapi` · `Bahasa perlu dipastikan`. Jangan memakai bahasa, genre, atau bentuk video sebagai status.

**When something is uncertain**, write it as it is: `Belum dipastikan` for the region, `Catatan bahasa terbuka` for `languageGroup`, and the reason in `context`.

## Filter URLs

Filters on `/jelajah/` are mirrored into the URL and can be combined:

```
/jelajah/?q=mambesak&bahasa=Sentani&genre=Lagu+rohani&wilayah=Saireri
```

Values match the data exactly — `bahasa` is `languageGroup` and `wilayah` is `customaryRegion`. Category tiles are plain links, so the page still works without JavaScript.

## Styling and theme

Tailwind v4 runs as a Vite plugin (`@tailwindcss/vite`). There is no `tailwind.config.mjs`; everything is in [`src/styles/global.css`](src/styles/global.css), imported by `Layout.astro`. Inter is the default interface font through `--font-sans`, while headings use Onest through `--font-heading`.

`dark:` keys off `data-theme` on `<html>`:

- A blocking inline script in `BaseHead.astro` sets it before first paint from `localStorage.theme`, falling back to the system preference. It must stay inline and in `<head>`.
- The header theme button saves the choice in `localStorage`; active styling is keyed off `data-theme` so it does not flash.
- Hand-written CSS needing a dark variant must use `[data-theme="dark"] .your-class` — those rules sit outside Tailwind's variant system.

**Renamed in v4**, and silently dead under the old names: `shadow-sm` → `shadow-xs`, bare `shadow` → `shadow-sm`, bare `rounded` → `rounded-sm`, bare `ring` → `ring-3`, `bg-gradient-to-*` → `bg-linear-to-*`.

## Client-side JavaScript

Search, filtering, expandable sections, and sidebar controls are small scripts against the DOM. No third-party CDN requests are used for interface behavior; thumbnails come from `i.ytimg.com`.

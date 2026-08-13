# Development guide

Technical notes for running, understanding, and adding to KastauMuzik. For an overview of the project, see [README.md](./README.md).

## Running locally

Requires Node.js 20+ and [pnpm](https://pnpm.io).

```bash
pnpm install
pnpm dev        # dev server at http://localhost:4321
pnpm build      # runs astro check, then a static build into dist/
pnpm preview    # preview the build output
```

`pnpm build` runs `astro check` first, so type errors fail the build.

## Structure

```
src/
├── data/collections.json     # the single source of collection content
├── lib/collections.ts        # derived data: shelf order, facets, filters, search text
├── types/index.d.ts          # CuratedVideo, MusicCollection, IndexedVideo
├── components/
│   ├── VideoCard.astro       # entry card (shelf and grid variants)
│   ├── CollectionShelf.astro # scroll-snap row with navigation buttons
│   ├── CategoryTile.astro    # coloured category tile on the browse page
│   └── Hero.astro, Navbar.astro, Footer.astro, BaseHead.astro
├── layouts/Layout.astro
└── pages/
    ├── index.astro, jelajah.astro, tentang.astro, pernyataan.astro
    └── koleksi/[slug].astro  # generated from every slug in collections.json
```

Every page reads `src/lib/collections.ts` rather than the JSON directly. Adding one recording to the JSON updates the counts, category tiles, filters, detail pages, and generated routes without touching another file.

Shelf order is set by `shelfOrder` in `src/lib/collections.ts`, not by the order in the JSON.

## Adding a recording

Add an object to the `videos` array of one shelf in [`src/data/collections.json`](src/data/collections.json):

```jsonc
{
  "slug": "awak-param-melani-sawaki",   // unique; becomes /koleksi/<slug>/
  "title": "Awak Param",
  "artist": "Melani Sawaki",
  "youtubeId": "5Lr68uxQS0o",
  "startSeconds": 8,                    // optional, for a chapter inside a compilation
  "endSeconds": 171,                    // optional
  "channel": "Geen Roger Ps",
  "region": "Biak",                     // regency or city
  "customaryRegion": "Saireri",         // one of the seven customary regions
  "language": "Biak",
  "languageGroup": "Biak",              // used as the language category
  "genres": ["Lagu daerah", "Pop Papua"],
  "year": "2021",
  "duration": "4:03",
  "curationStatus": "Kanal warga",      // badge shown on the card thumbnail
  "note": "One-sentence summary, used as the meta description.",
  "description": "A paragraph about the recording.",
  "context": "Where this information came from, and what is still uncertain."
}
```

Take the title, channel name, upload year, and duration from YouTube's metadata rather than estimating them:

```bash
curl -s "https://www.youtube.com/oembed?url=https://youtu.be/<id>&format=json"
```

Note that user-facing values inside the data stay in Indonesian — they are rendered directly on the site.

### Customary region vocabulary

Use one of the seven customary regions of Tanah Papua: `Mamta`, `Saireri`, `Domberai`, `Bomberai`, `Ha Anim`, `La Pago`, `Mee Pago`.

Two extra markers keep the metadata honest:

| Value | Use when |
| --- | --- |
| `Belum dipastikan` | The source does not state where the recording is from |
| `Lintas wilayah adat` | A compilation spanning several regions at once |

Categories are derived from the data, so a region with no recordings yet simply does not appear as a tile on `/jelajah/`.

### Song type vocabulary

Reuse the existing terms so categories do not fragment:

`Lagu daerah` · `Lagu tarian` · `Lagu rohani` · `Paduan suara` · `Pop Papua` · `Rock Papua` · `Rekaman arsip` · `Arsip Mambesak` · `Rekaman panggung` · `Versi cover` · `Video lirik`

Some of these map to the "how to listen" filter chips on `/jelajah/` through `modesForVideo` in [`src/lib/collections.ts`](src/lib/collections.ts):

| Chip | Triggered by |
| --- | --- |
| Bahasa daerah | Any `languageGroup` other than `Bahasa Indonesia` |
| Rekaman arsip | `Rekaman arsip`, `Arsip Mambesak` |
| Panggung & koor | `Rekaman panggung`, `Paduan suara` |
| Lagu rohani | `Lagu rohani` |

If you introduce a new term that belongs to one of those chips, update `modesForVideo` as well.

### When something is uncertain

Write it as it is. Use `Belum dipastikan` for the region or `Catatan bahasa terbuka` for `languageGroup`, then explain in `context` why the information is still open.

## Filter URL parameters

Filters on `/jelajah/` are mirrored into the URL, so any view can be linked:

```
/jelajah/?q=mambesak
/jelajah/?bahasa=Sentani
/jelajah/?genre=Lagu+rohani
/jelajah/?wilayah=Saireri
/jelajah/?rak=Rohani+dan+suara+koor
/jelajah/?mode=arsip
```

Parameters can be combined. Values match the data exactly — `bahasa` matches `languageGroup`, `wilayah` matches `customaryRegion`, and `rak` matches the shelf title.

Category tiles are plain links, so the page is still browsable without JavaScript. With JavaScript enabled, those links filter in place instead of reloading.

## Tech

[Astro](https://astro.build) · [Tailwind CSS](https://tailwindcss.com) · [Alpine.js](https://alpinejs.dev) · TypeScript.

The output is a static site with no third-party CDN requests at runtime. Search, filtering, and the scrolling shelves are small per-page scripts written against the DOM directly; shelves use native CSS `scroll-snap` rather than a carousel library. Alpine drives the small-screen navigation menu in `Navbar.astro` and is the only client framework in the bundle. Thumbnails are loaded directly from `i.ytimg.com`.

Alpine is registered through the [`@astrojs/alpinejs`](https://docs.astro.build/en/guides/integrations-guide/alpinejs/) integration in `astro.config.mjs`, so directives work in any `.astro` file without an import. Only Alpine core is installed — if you reach for a plugin such as `@alpinejs/collapse`, register it through an integration entrypoint rather than a script tag.

Elements hidden by `x-show` need `x-cloak` so they do not flash before Alpine hydrates; the matching `[x-cloak] { display: none }` rule lives in `Navbar.astro`.

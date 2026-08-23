/**
 * Reads the archive from the Django API on every request.
 *
 * Runs in the Worker, never in a visitor's browser. Maps the API's snake_case
 * onto the camelCase shape the pages use.
 */

import { env } from "cloudflare:workers";

import type { CuratedVideo, IndexedVideo, MusicCollection } from "@/types/index";

/** One page of a DRF-paginated list. */
type Paginated<T> = {
  count: number;
  next: string | null;
  results: T[];
};

type ApiCollection = {
  slug: string;
  title: string;
  order: number;
};

type ApiVideo = {
  slug: string;
  title: string;
  artist: string;
  youtube_id: string;
  collection: string;
  region: string;
  customary_region: string;
  language: string;
  formats: string[];
  year: string;
  duration: string;
  note: string;
  description: string;
  context: string;
  is_featured: boolean;
  related: string[];
};

export type Catalog = {
  collections: MusicCollection[];
  videos: IndexedVideo[];
  /** Ranked related slugs per video, scored by the API. */
  relatedBySlug: Map<string, string[]>;
  featuredSlugs: string[];
};

/**
 * Where the API lives, read per request rather than baked in at build time, so
 * it can move without redeploying. Set as a Worker variable in production;
 * .env is the local fallback.
 */
const apiOrigin = () =>
  (env.API_ORIGIN ?? import.meta.env.API_ORIGIN ?? "").replace(/\/$/, "");

/** Fetch every page of a paginated list endpoint, following `next`. */
const fetchAllPages = async <T>(path: string): Promise<T[]> => {
  const results: T[] = [];
  let url: string | null = `${apiOrigin()}/api/v1${path}`;

  while (url) {
    const response: Response = await fetch(url);

    if (!response.ok) {
      throw new Error(
        `${response.status} ${response.statusText} dari ${url}`,
      );
    }

    const page: Paginated<T> = await response.json();
    results.push(...page.results);
    url = page.next;
  }

  return results;
};

const toCuratedVideo = (video: ApiVideo): CuratedVideo => ({
  slug: video.slug,
  title: video.title,
  artist: video.artist,
  youtubeId: video.youtube_id,
  region: video.region,
  customaryRegion: video.customary_region,
  language: video.language,
  formats: video.formats,
  // The API sends "" for an unknown year or duration.
  year: video.year || undefined,
  duration: video.duration || undefined,
  note: video.note,
  description: video.description,
  context: video.context,
});

export const loadCatalog = async (): Promise<Catalog> => {
  const origin = apiOrigin();

  if (!origin) {
    throw new Error(
      "API_ORIGIN belum diatur. Salin apps/web/.env.example ke apps/web/.env, " +
        "lalu jalankan API-nya (pnpm --filter api dev).",
    );
  }

  let apiCollections: ApiCollection[];
  let apiVideos: ApiVideo[];

  try {
    [apiCollections, apiVideos] = await Promise.all([
      fetchAllPages<ApiCollection>("/collections/"),
      fetchAllPages<ApiVideo>("/videos/"),
    ]);
  } catch (cause) {
    throw new Error(
      `Gagal mengambil katalog dari ${origin}. ` +
        `Penyebab: ${cause instanceof Error ? cause.message : String(cause)}`,
    );
  }

  const videosByCollection = new Map<string, IndexedVideo[]>();
  for (const video of apiVideos) {
    const indexed: IndexedVideo = {
      ...toCuratedVideo(video),
      collectionId: video.collection,
    };
    const bucket = videosByCollection.get(video.collection);
    if (bucket) bucket.push(indexed);
    else videosByCollection.set(video.collection, [indexed]);
  }

  // Shelf order comes from the `order` column curators control.
  const ordered = [...apiCollections].sort(
    (a, b) => a.order - b.order || a.slug.localeCompare(b.slug),
  );

  const collections: MusicCollection[] = ordered.map((collection) => ({
    id: collection.slug,
    title: collection.title,
    videos: videosByCollection.get(collection.slug) ?? [],
  }));

  return {
    collections,
    // From the buckets, not `collections`, whose `videos` are CuratedVideo and
    // would drop `collectionId`.
    videos: ordered.flatMap(
      (collection) => videosByCollection.get(collection.slug) ?? [],
    ),
    relatedBySlug: new Map(
      apiVideos.map((video) => [video.slug, video.related]),
    ),
    // Kept in the order the API sent them.
    featuredSlugs: apiVideos
      .filter((video) => video.is_featured)
      .map((video) => video.slug),
  };
};

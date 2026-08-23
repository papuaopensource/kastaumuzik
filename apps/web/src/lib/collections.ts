/**
 * The catalogue, as the pages see it.
 *
 * Read on every request. The result is not memoised: module state in a Worker
 * lives as long as the isolate, so caching it here would serve a stale archive
 * for minutes or hours after a curator publishes.
 */

import { loadCatalog, type Catalog } from "@/lib/catalog";
import type { IndexedVideo, MusicCollection } from "@/types/index";

export type SiteCatalog = {
  collections: MusicCollection[];
  allVideos: IndexedVideo[];
  videoCount: number;
  /** Related videos for a slug, already ordered by relevance by the API. */
  relatedVideosFor(slug: string): IndexedVideo[];
  /** Curator picks, most prominent first. */
  featuredVideos: IndexedVideo[];
};

const build = async (): Promise<SiteCatalog> => {
  const catalog: Catalog = await loadCatalog();
  const bySlug = new Map(catalog.videos.map((video) => [video.slug, video]));

  const resolve = (slugs: string[]) =>
    slugs
      .map((slug) => bySlug.get(slug))
      .filter((video): video is IndexedVideo => video !== undefined);

  return {
    collections: catalog.collections,
    allVideos: catalog.videos,
    videoCount: catalog.videos.length,
    relatedVideosFor: (slug) => resolve(catalog.relatedBySlug.get(slug) ?? []),
    featuredVideos: resolve(catalog.featuredSlugs),
  };
};

/** The catalogue as it stands right now. One read per request. */
export const getCatalog = (): Promise<SiteCatalog> => build();

/** Per-field text, so client-side search can weigh a title above the rest. */
export const searchFields = (video: IndexedVideo) => ({
  "data-title": video.title.toLocaleLowerCase("id"),
  "data-artist": video.artist.toLocaleLowerCase("id"),
});

export const searchTextFor = (video: IndexedVideo) =>
  [
    video.title,
    video.artist,
    video.region,
    video.customaryRegion,
    video.language,
    video.formats.join(" "),
    video.note,
  ]
    .join(" ")
    .toLocaleLowerCase("id");

/**
 * Avatar palette. All dark enough for white text, and picked deterministically
 * from the seed so colours are stable across builds.
 */
const tilePalette = [
  "#8a3b2c",
  "#1f5b4a",
  "#3a3f86",
  "#9c3450",
  "#4c5a24",
  "#28607c",
  "#6f3a86",
  "#a9522a",
  "#3d5a78",
  "#6a3555",
  "#2f6152",
  "#7c3b3b",
];

export const tileColor = (seed: string) => {
  let hash = 0;
  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash * 31 + seed.charCodeAt(index)) % 100000;
  }
  return tilePalette[hash % tilePalette.length];
};

import collectionData from "@/data/collections.json";
import type { IndexedVideo, MusicCollection } from "@/types/index";

/** A source video is one catalog item. Chapters inside a compilation are not separate entries. */
const sourceIds = collectionData.flatMap((collection) =>
  collection.videos.map((video) => video.youtubeId),
);
const duplicateSourceIds = sourceIds.filter(
  (youtubeId, index) => sourceIds.indexOf(youtubeId) !== index,
);

if (duplicateSourceIds.length > 0) {
  throw new Error(
    `Setiap video YouTube hanya boleh menjadi satu entri. Duplikat: ${[...new Set(duplicateSourceIds)].join(", ")}`,
  );
}

/** Shelves ordered from the broadest entry point to the most specific. */
const shelfOrder = [
  "arsip-dan-jejak-musik",
  "lagu-daerah-dan-penampilan",
  "pop-dan-cover-papua",
  "rohani-dan-paduan-suara",
];

export const collections = (collectionData as MusicCollection[])
  .slice()
  .sort((a, b) => shelfOrder.indexOf(a.id) - shelfOrder.indexOf(b.id));

export const allVideos: IndexedVideo[] = collections.flatMap((collection) =>
  collection.videos.map((video) => ({
    ...video,
    collectionId: collection.id,
  })),
);

export const videoCount = allVideos.length;

/**
 * Placeholders that record missing information rather than name a real
 * category. They belong in a curation note, not in a badge or a filter link.
 */
const openEnded = new Set([
  "Belum dipastikan",
  "Catatan bahasa terbuka",
  "Lintas wilayah adat",
  "Beragam bahasa Papua",
  "Bahasa daerah Papua",
]);

export const isSpecific = (value: string) => !openEnded.has(value);

export const searchTextFor = (video: IndexedVideo) =>
  [
    video.title,
    video.artist,
    video.channel,
    video.region,
    video.customaryRegion,
    video.language,
    video.languageGroup,
    video.genres.join(" "),
    video.formats.join(" "),
    video.note,
  ]
    .join(" ")
    .toLocaleLowerCase("id");

/**
 * Avatar palette. All dark enough for white text, and picked
 * deterministically from the facet name so colours are stable across builds.
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

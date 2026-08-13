import collectionData from "../data/collections.json";
import type { CuratedVideo, Facet, IndexedVideo, MusicCollection } from "../types/index";

/** Urutan rak dari pintu masuk paling umum ke koleksi yang lebih khusus. */
const shelfOrder = [
  "pilihan-untuk-mulai",
  "lima-belas-bahasa-mambesak",
  "ingatan-bersama",
  "suara-dari-kanal-warga",
  "nyanyian-jemaat",
];

export const collections = (collectionData as MusicCollection[])
  .slice()
  .sort((a, b) => shelfOrder.indexOf(a.id) - shelfOrder.indexOf(b.id));

export const allVideos: IndexedVideo[] = collections.flatMap((collection) =>
  collection.videos.map((video) => ({
    ...video,
    collectionId: collection.id,
    collectionTitle: collection.title,
  })),
);

export const videoCount = allVideos.length;

/** Cara mendengar: penyaring cepat yang memotong lintas rak di halaman jelajah. */
export const modesForVideo = (video: CuratedVideo) =>
  [
    video.languageGroup !== "Bahasa Indonesia" ? "bahasa-daerah" : "",
    video.genres.some((genre) => ["Rekaman arsip", "Arsip Mambesak"].includes(genre)) ? "arsip" : "",
    video.genres.some((genre) => ["Rekaman panggung", "Paduan suara"].includes(genre)) ? "penampilan" : "",
    video.genres.includes("Lagu rohani") ? "rohani" : "",
  ].filter(Boolean);

export const modeLabels: Array<{ id: string; label: string }> = [
  { id: "all", label: "Semua" },
  { id: "bahasa-daerah", label: "Bahasa daerah" },
  { id: "arsip", label: "Rekaman arsip" },
  { id: "penampilan", label: "Panggung & koor" },
  { id: "rohani", label: "Lagu rohani" },
];

export const modeOptions = modeLabels.map((mode) => ({
  ...mode,
  count:
    mode.id === "all"
      ? videoCount
      : allVideos.filter((video) => modesForVideo(video).includes(mode.id)).length,
}));

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
    video.collectionTitle,
    video.curationStatus,
    video.note,
  ]
    .join(" ")
    .toLocaleLowerCase("id");

const tally = (values: string[]): Facet[] => {
  const counts = new Map<string, number>();
  values.forEach((value) => counts.set(value, (counts.get(value) ?? 0) + 1));

  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "id"));
};

export const collectionFacets = collections.map((collection) => ({
  name: collection.title,
  count: collection.videos.length,
  id: collection.id,
  coverId: collection.videos[0].youtubeId,
}));

export const languageFacets = tally(allVideos.map((video) => video.languageGroup));
export const genreFacets = tally(allVideos.flatMap((video) => video.genres));
export const regionFacets = tally(allVideos.map((video) => video.customaryRegion));

/** Satu contoh sampul per faset supaya kartu kategori punya wajah. */
export const coverFor = (predicate: (video: IndexedVideo) => boolean) =>
  (allVideos.find(predicate) ?? allVideos[0]).youtubeId;

/**
 * Palet kartu kategori. Semua warna gelap agar teks putih tetap terbaca,
 * dan dipilih deterministik dari nama faset supaya tidak berubah antar build.
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

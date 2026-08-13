export type CuratedVideo = {
  slug: string;
  title: string;
  artist: string;
  youtubeId: string;
  startSeconds?: number;
  endSeconds?: number;
  channel: string;
  region: string;
  customaryRegion: string;
  language: string;
  languageGroup: string;
  genres: string[];
  year: string;
  duration: string;
  curationStatus: string;
  note: string;
  description: string;
  context: string;
};

export type MusicCollection = {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
  videos: CuratedVideo[];
};

/** Video yang sudah tahu asal raknya — dipakai di kartu, rak, dan hasil pencarian. */
export type IndexedVideo = CuratedVideo & {
  collectionId: string;
  collectionTitle: string;
};

export type Facet = {
  name: string;
  count: number;
};

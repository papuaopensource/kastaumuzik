export type CuratedVideo = {
  slug: string;
  title: string;
  artist: string;
  youtubeId: string;
  channel: string;
  region: string;
  customaryRegion: string;
  language: string;
  languageGroup: string;
  genres: string[];
  formats: string[];
  year?: string;
  duration?: string;
  note: string;
  description: string;
  context: string;
};

export type MusicCollection = {
  id: string;
  title: string;
  videos: CuratedVideo[];
};

/** A video that knows which shelf it came from. Used by cards, shelves, and search results. */
export type IndexedVideo = CuratedVideo & {
  collectionId: string;
};

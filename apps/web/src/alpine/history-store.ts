/**
 * Watch history, shared by every page that reads it.
 *
 * Lives only in the visitor's browser and is never sent anywhere.
 */

import type { Alpine } from "alpinejs";

const STORAGE_KEY = "kastaumuzik:watch-history";
const MAX_ENTRIES = 50;

export type HistoryStore = {
  slugs: string[];
  init(): void;
  read(): string[];
  persist(): void;
  record(slug: string): void;
  remove(slug: string): void;
  clear(): void;
  recent(count: number): string[];
  has(slug: string): boolean;
};

export const registerHistoryStore = (Alpine: Alpine) => {
  Alpine.store("history", {
    slugs: [] as string[],

    init() {
      this.slugs = this.read();

      // Keeps tabs in step with each other.
      window.addEventListener("storage", (event: StorageEvent) => {
        if (event.key === STORAGE_KEY) this.slugs = this.read();
      });
    },

    read(): string[] {
      try {
        const saved: unknown = JSON.parse(
          localStorage.getItem(STORAGE_KEY) ?? "[]",
        );
        return Array.isArray(saved)
          ? saved.filter((slug): slug is string => typeof slug === "string")
          : [];
      } catch {
        // Private windows and blocked site data land here.
        return [];
      }
    },

    persist() {
      try {
        if (this.slugs.length === 0) localStorage.removeItem(STORAGE_KEY);
        else localStorage.setItem(STORAGE_KEY, JSON.stringify(this.slugs));
      } catch {
        // Storage unavailable; the in-memory list still drives this page.
      }
    },

    record(slug: string) {
      this.slugs = [slug, ...this.slugs.filter((s: string) => s !== slug)].slice(
        0,
        MAX_ENTRIES,
      );
      this.persist();
    },

    remove(slug: string) {
      this.slugs = this.slugs.filter((s: string) => s !== slug);
      this.persist();
    },

    clear() {
      this.slugs = [];
      this.persist();
    },

    recent(count: number): string[] {
      return this.slugs.slice(0, count);
    },

    has(slug: string): boolean {
      return this.slugs.includes(slug);
    },
  } satisfies HistoryStore);
};

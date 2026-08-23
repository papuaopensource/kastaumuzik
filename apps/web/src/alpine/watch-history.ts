/**
 * The history page: list what this browser watched, search it, remove entries.
 *
 * Reads the shared `history` store rather than parsing localStorage again.
 */

import type { Alpine } from "alpinejs";

import type { HistoryStore } from "./history-store";

const normalise = (value: string) =>
  value
    .toLocaleLowerCase("id")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .trim();

type Entry = { element: HTMLElement; slug: string; haystack: string };

export const registerWatchHistory = (Alpine: Alpine) => {
  Alpine.data("watchHistory", () => ({
    query: "",
    entries: [] as Entry[],
    matchCount: 0,

    init() {
      this.entries = Array.from(
        this.$el.querySelectorAll<HTMLElement>("[data-history-item]"),
      ).map((element) => ({
        element,
        slug: element.dataset.videoSlug ?? "",
        haystack: normalise(element.dataset.historySearch ?? ""),
      }));

      this.render();

      // Re-render whenever the stored list changes, including from another tab.
      this.$watch("query", () => this.render());
      Alpine.effect(() => {
        // Touching `slugs` subscribes this effect to store changes.
        void (Alpine.store("history") as HistoryStore).slugs.length;
        this.render();
      });

      window.addEventListener("pageshow", (event: PageTransitionEvent) => {
        if (event.persisted) this.render();
      });
    },

    get history(): string[] {
      return (Alpine.store("history") as HistoryStore).slugs;
    },

    get total(): number {
      return this.history.length;
    },

    get isEmpty(): boolean {
      return this.matchCount === 0;
    },

    get emptyTitle(): string {
      return this.total === 0 ? "Belum ada riwayat" : "Tidak ada hasil";
    },

    get emptyDescription(): string {
      return this.total === 0
        ? "Video yang kamu buka akan muncul di halaman ini."
        : `Tidak ada riwayat yang cocok dengan “${this.query.trim()}”.`;
    },

    render() {
      const list = this.$refs.list as HTMLElement | undefined;
      if (!list) return;

      const query = normalise(this.query);
      const bySlug = new Map(this.entries.map((entry) => [entry.slug, entry]));

      this.entries.forEach((entry) => entry.element.classList.add("hidden"));

      // Most recently watched first, the order the store keeps.
      const matches = this.history
        .map((slug) => bySlug.get(slug))
        .filter(
          (entry): entry is Entry =>
            entry !== undefined && entry.haystack.includes(query),
        );

      matches.forEach((entry) => {
        entry.element.classList.remove("hidden");
        list.append(entry.element);
      });

      this.matchCount = matches.length;
    },

    remove(slug: string) {
      (Alpine.store("history") as HistoryStore).remove(slug);
      this.announce("Video dihapus dari riwayat.");
    },

    clearAll() {
      if (this.total === 0) return;
      if (!window.confirm("Hapus semua riwayat tontonan di perangkat ini?")) return;

      (Alpine.store("history") as HistoryStore).clear();
      this.query = "";
      this.announce("Semua riwayat telah dihapus.");
    },

    announce(message: string) {
      const status = this.$refs.status as HTMLElement | undefined;
      if (status) status.textContent = message;
    },
  }));
};

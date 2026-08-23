/**
 * The home feed: filter chips, endless scroll, and a fresh shuffle every visit.
 *
 * The cards are rendered by Astro and already in the page; this only decides
 * which are shown and in what order. The order is pure chance, with no memory
 * of what this browser watched. Anything history-driven lives on /jelajah/.
 */

import type { Alpine } from "alpinejs";

type FeedItem = {
  element: HTMLElement;
  collection: string;
  formats: string[];
};

const readItems = (root: HTMLElement): FeedItem[] =>
  Array.from(root.querySelectorAll<HTMLElement>("[data-home-video]")).map(
    (element) => ({
      element,
      collection: element.dataset.collection ?? "",
      formats: (element.dataset.formats ?? "").split("|").filter(Boolean),
    }),
  );

/** Filters are `collection:<slug>` or `format:<name>`, built by the page. */
const matchesFilter = (item: FeedItem, filter: string): boolean => {
  if (filter === "all") return true;

  const separator = filter.indexOf(":");
  const kind = filter.slice(0, separator);
  const value = filter.slice(separator + 1);

  if (kind === "collection") return item.collection === value;
  if (kind === "format") return item.formats.includes(value);
  return true;
};

/** Fisher–Yates, on a copy so the source order is left alone. */
const shuffle = <T>(items: T[]): T[] => {
  const shuffled = [...items];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const target = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[target]] = [shuffled[target], shuffled[index]];
  }
  return shuffled;
};

export const registerHomeFeed = (Alpine: Alpine) => {
  Alpine.data("homeFeed", () => ({
    activeFilter: "all",
    items: [] as FeedItem[],
    ordered: [] as FeedItem[],
    visibleCount: 0,
    batchSize: 8,
    exhausted: false,

    init() {
      this.items = readItems(this.$el);
      this.batchSize = window.matchMedia("(min-width: 1536px)").matches
        ? 16
        : window.matchMedia("(min-width: 1280px)").matches
          ? 12
          : 8;

      this.render();

      const sentinel = this.$refs.sentinel as HTMLElement | undefined;
      if (sentinel && "IntersectionObserver" in window) {
        new IntersectionObserver(
          (entries) => {
            if (entries.some((entry) => entry.isIntersecting)) this.showMore();
          },
          { rootMargin: "200px 0px" },
        ).observe(sentinel);
      } else {
        // No observer: show everything, since nothing can reveal more later.
        this.ordered.forEach((item) => item.element.classList.remove("hidden"));
        this.visibleCount = this.ordered.length;
        this.exhausted = true;
      }
    },

    setFilter(filter: string) {
      this.activeFilter = filter;
      this.render();
    },

    render() {
      this.items.forEach((item) => item.element.classList.add("hidden"));

      this.ordered = shuffle(
        this.items.filter((item) => matchesFilter(item, this.activeFilter)),
      );

      const feed = this.$refs.feed as HTMLElement;
      this.ordered.forEach((item) => feed.append(item.element));

      this.visibleCount = 0;
      this.exhausted = false;
      this.showMore();
    },

    showMore() {
      const next = this.ordered.slice(
        this.visibleCount,
        this.visibleCount + this.batchSize,
      );
      next.forEach((item) => item.element.classList.remove("hidden"));
      this.visibleCount += next.length;
      this.exhausted = this.visibleCount >= this.ordered.length;
    },
  }));
};

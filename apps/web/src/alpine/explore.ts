/**
 * Search on the Jelajah page.
 *
 * Scores each field separately and sorts by the result. No index and no
 * library: scoring thirty cards on each keystroke is cheap at this size.
 */

import type { Alpine } from "alpinejs";

import type { HistoryStore } from "./history-store";

/** How many watched videos the "continue watching" row brings back. */
const CONTINUE_ROW_LIMIT = 12;

/** Weights, highest first. A title beats an artist beats a passing mention. */
const SCORE_TITLE_PREFIX = 12;
const SCORE_TITLE_MATCH = 8;
const SCORE_ARTIST_PREFIX = 7;
const SCORE_ARTIST_MATCH = 5;
const SCORE_FACET_MATCH = 2;
/** Anything the concatenated blob catches but the fields above do not. */
const SCORE_OTHER_MATCH = 1;

const normalise = (value: string) =>
  value
    .toLocaleLowerCase("id")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .trim();

type Card = {
  element: HTMLElement;
  title: string;
  artist: string;
  facets: string;
  all: string;
};

const scoreCard = (card: Card, query: string): number => {
  let score = 0;

  if (card.title.startsWith(query)) score += SCORE_TITLE_PREFIX;
  else if (card.title.includes(query)) score += SCORE_TITLE_MATCH;

  if (card.artist.startsWith(query)) score += SCORE_ARTIST_PREFIX;
  else if (card.artist.includes(query)) score += SCORE_ARTIST_MATCH;

  if (card.facets.includes(query)) score += SCORE_FACET_MATCH;
  if (score === 0 && card.all.includes(query)) score += SCORE_OTHER_MATCH;

  return score;
};

export const registerExplore = (Alpine: Alpine) => {
  Alpine.data("explore", () => ({
    query: "",
    matchCount: 0,
    continueCount: 0,
    cards: [] as Card[],

    init() {
      // Scoped to the results grid: the browse shelves below render the same
      // videos again, and scanning $el would collect both copies.
      const grid = this.$refs.grid as HTMLElement;
      this.cards = Array.from(
        grid.querySelectorAll<HTMLElement>("[data-video-card]"),
      ).map((element) => ({
        element,
        title: normalise(element.dataset.title ?? ""),
        artist: normalise(element.dataset.artist ?? ""),
        facets: normalise(
          [
            element.dataset.language,
            element.dataset.region,
            element.dataset.collection,
            element.dataset.formats?.replaceAll("|", " "),
          ]
            .filter(Boolean)
            .join(" "),
        ),
        all: normalise(element.dataset.search ?? ""),
      }));

      this.renderContinueWatching();
      this.readUrl();
      this.apply({ pushUrl: false });

      window.addEventListener("popstate", () => {
        this.readUrl();
        this.apply({ pushUrl: false });
      });
    },

    /**
     * "Lanjutkan menonton", built by cloning cards already on the page. Which
     * videos belong here is only known in the browser.
     */
    renderContinueWatching() {
      const row = this.$refs.continueRow as HTMLElement | undefined;
      if (!row) return;

      const history = Alpine.store("history") as HistoryStore;
      const bySlug = new Map(
        this.cards.map((card) => [card.element.dataset.slug ?? "", card]),
      );

      row.replaceChildren();

      for (const slug of history.recent(CONTINUE_ROW_LIMIT)) {
        const source = bySlug.get(slug);
        if (!source) continue;

        const clone = source.element.cloneNode(true) as HTMLElement;
        clone.hidden = false;
        // Must not answer to searches.
        clone.removeAttribute("data-video-card");
        clone.classList.add("w-68", "shrink-0", "snap-start", "sm:w-72");
        row.append(clone);
      }

      this.continueCount = row.childElementCount;
    },

    get isSearching(): boolean {
      return this.query.trim().length > 0;
    },

    get isEmpty(): boolean {
      return this.isSearching && this.matchCount === 0;
    },

    readUrl() {
      this.query = new URLSearchParams(window.location.search).get("q") ?? "";
    },

    writeUrl() {
      const trimmed = this.query.trim();
      const search = trimmed ? `?${new URLSearchParams({ q: trimmed })}` : "";
      window.history.replaceState(
        null,
        "",
        search || window.location.pathname,
      );
    },

    apply({ pushUrl = true } = {}) {
      const query = normalise(this.query);

      if (query) {
        const grid = this.$refs.grid as HTMLElement;
        const scored = this.cards
          .map((card) => ({ card, score: scoreCard(card, query) }))
          .filter((entry) => entry.score > 0)
          .sort(
            (a, b) =>
              b.score - a.score ||
              a.card.title.localeCompare(b.card.title, "id"),
          );

        this.cards.forEach((card) => {
          card.element.hidden = true;
        });
        scored.forEach(({ card }) => {
          card.element.hidden = false;
          grid.append(card.element);
        });

        this.matchCount = scored.length;
      }

      if (pushUrl) this.writeUrl();
    },

    reset() {
      this.query = "";
      this.apply();
      (this.$refs.input as HTMLInputElement)?.focus();
    },

    /** "/" focuses search, Escape leaves it — both skipped while typing. */
    onKeydown(event: KeyboardEvent) {
      const input = this.$refs.input as HTMLInputElement;
      const tag = document.activeElement?.tagName;

      if (
        event.key === "/" &&
        document.activeElement !== input &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(tag ?? "")
      ) {
        event.preventDefault();
        input?.focus();
      }

      if (event.key === "Escape" && document.activeElement === input) {
        this.reset();
        input?.blur();
      }
    },
  }));
};

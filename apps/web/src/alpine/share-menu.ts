/**
 * Share popover on the watch page, plus recording the view in history.
 *
 * The links need the page URL and the caret needs measuring, so both are done
 * in the browser.
 */

import type { Alpine } from "alpinejs";

import type { HistoryStore } from "./history-store";

export const registerShareMenu = (Alpine: Alpine) => {
  Alpine.data("watchPage", (slug: string) => ({
    open: false,
    copyLabel: "Salin tautan",

    init() {
      if (slug) (Alpine.store("history") as HistoryStore).record(slug);
    },

    get pageUrl(): string {
      return window.location.href;
    },

    get shareText(): string {
      const heading = document.querySelector("h1")?.textContent?.trim();
      return `${heading ?? document.title} - kastaumuzik`;
    },

    shareHref(platform: string): string {
      const url = encodeURIComponent(this.pageUrl);
      const text = encodeURIComponent(this.shareText);
      switch (platform) {
        case "whatsapp":
          return `https://wa.me/?text=${encodeURIComponent(`${this.shareText}\n${this.pageUrl}`)}`;
        case "facebook":
          return `https://www.facebook.com/sharer/sharer.php?u=${url}`;
        case "x":
          return `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
        default:
          return this.pageUrl;
      }
    },

    toggle() {
      this.open = !this.open;
      if (this.open) {
        this.$nextTick(() => {
          this.position();
          this.$refs.popover
            ?.querySelector<HTMLElement>("[role='menuitem']")
            ?.focus();
        });
      }
    },

    close({ returnFocus = false } = {}) {
      if (!this.open) return;
      this.open = false;
      if (returnFocus) (this.$refs.trigger as HTMLElement)?.focus();
    },

    /** Keeps the caret pointing at the button on every viewport width. */
    position() {
      const trigger = this.$refs.trigger as HTMLElement | undefined;
      const popover = this.$refs.popover as HTMLElement | undefined;
      if (!trigger || !popover || !this.open) return;

      const triggerRect = trigger.getBoundingClientRect();

      if (!window.matchMedia("(min-width: 640px)").matches) {
        popover.style.top = `${triggerRect.bottom + 12}px`;
      } else {
        popover.style.removeProperty("top");
      }

      const popoverRect = popover.getBoundingClientRect();
      const caretLeft = Math.min(
        Math.max(
          triggerRect.left + triggerRect.width / 2 - popoverRect.left,
          18,
        ),
        popoverRect.width - 18,
      );
      popover.style.setProperty("--share-caret-left", `${caretLeft}px`);
    },

    async copyLink() {
      try {
        await navigator.clipboard.writeText(this.pageUrl);
        this.copyLabel = "Tersalin";
        window.setTimeout(() => {
          this.copyLabel = "Salin tautan";
        }, 1800);
      } catch {
        window.prompt("Salin tautan ini", this.pageUrl);
      }
    },
  }));
};

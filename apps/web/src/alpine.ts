/**
 * Alpine entrypoint, loaded by @astrojs/alpinejs.
 *
 * Everything here enhances markup Astro already rendered; none of it draws the
 * catalogue. The theme script in BaseHead.astro stays outside Alpine because it
 * must run before first paint.
 */

import type { Alpine } from "alpinejs";

import { registerExplore } from "@/alpine/explore";
import { registerHistoryStore } from "@/alpine/history-store";
import { registerHomeFeed } from "@/alpine/home-feed";
import { registerShareMenu } from "@/alpine/share-menu";
import { registerSubmissionForm } from "@/alpine/submission-form";
import { registerWatchHistory } from "@/alpine/watch-history";

export default (Alpine: Alpine) => {
  // Registered first: components read it during their own init().
  registerHistoryStore(Alpine);

  registerHomeFeed(Alpine);
  registerExplore(Alpine);
  registerWatchHistory(Alpine);
  registerSubmissionForm(Alpine);
  registerShareMenu(Alpine);
};

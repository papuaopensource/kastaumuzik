/**
 * The submission form. Posts to /api/submissions, which forwards to Django.
 *
 * The draft is kept in localStorage and cleared once a submission is accepted.
 */

import type { Alpine } from "alpinejs";

const DRAFT_KEY = "kastaumuzik:submission-draft";

const ALLOWED_HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtu.be",
  "www.youtu.be",
]);

/** A local check for fast feedback; Django re-validates and owns the verdict. */
const looksLikeYoutube = (value: string): boolean => {
  if (!value) return true;
  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol)) return false;
    if (!ALLOWED_HOSTS.has(url.hostname)) return false;

    if (url.hostname.endsWith("youtu.be")) {
      return url.pathname.split("/").filter(Boolean).length > 0;
    }
    return (
      (url.pathname === "/watch" && Boolean(url.searchParams.get("v"))) ||
      /^\/(shorts|live)\/[^/]+/.test(url.pathname)
    );
  } catch {
    return false;
  }
};

type Status = "idle" | "sending" | "sent" | "error";

export const registerSubmissionForm = (Alpine: Alpine) => {
  Alpine.data("submissionForm", () => ({
    form: {
      youtube_url: "",
      title: "",
      performer: "",
      description: "",
      // Honeypot, hidden from people.
      website: "",
    },
    status: "idle" as Status,
    message: "",
    fieldErrors: {} as Record<string, string>,

    init() {
      this.restoreDraft();
      // Alpine watches reactive objects deeply, so no option is needed.
      this.$watch("form", () => this.saveDraft());
    },

    get sending(): boolean {
      return this.status === "sending";
    },

    get hasDraft(): boolean {
      return Object.entries(this.form).some(
        ([field, value]) => field !== "website" && value !== "",
      );
    },

    validateUrl() {
      const input = this.$refs.url as HTMLInputElement | undefined;
      const valid = looksLikeYoutube(this.form.youtube_url);
      input?.setCustomValidity(
        valid ? "" : "Masukkan tautan video YouTube yang valid.",
      );
      return valid;
    },

    async submit() {
      const element = this.$el as HTMLFormElement;
      this.validateUrl();
      if (!element.checkValidity()) {
        element.reportValidity();
        return;
      }

      this.status = "sending";
      this.message = "";
      this.fieldErrors = {};

      try {
        const response = await fetch("/api/submissions", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(this.form),
        });
        const payload = await response.json().catch(() => ({}));

        if (response.ok) {
          this.status = "sent";
          this.message =
            payload.detail ?? "Terima kasih. Usulan kamu akan ditinjau kurator.";
          this.reset({ keepMessage: true });
          return;
        }

        this.status = "error";

        if (response.status === 429) {
          this.message =
            "Terlalu banyak usulan dari jaringan ini. Coba lagi nanti.";
          return;
        }

        // DRF reports per-field errors as { field: [message, …] }.
        const errors: Record<string, string> = {};
        for (const [field, value] of Object.entries(payload)) {
          if (field === "detail") continue;
          errors[field] = Array.isArray(value) ? String(value[0]) : String(value);
        }
        this.fieldErrors = errors;
        this.message =
          payload.detail ??
          (Object.keys(errors).length
            ? "Periksa kembali isian yang ditandai."
            : "Usulan gagal dikirim. Coba lagi.");
      } catch {
        this.status = "error";
        this.message =
          "Tidak dapat menghubungi server. Periksa koneksi lalu coba lagi.";
      }
    },

    reset({ keepMessage = false } = {}) {
      this.form = {
        youtube_url: "",
        title: "",
        performer: "",
        description: "",
        website: "",
      };
      this.fieldErrors = {};
      if (!keepMessage) {
        this.status = "idle";
        this.message = "";
      }
      this.clearDraft();
      (this.$refs.url as HTMLInputElement)?.setCustomValidity("");
    },

    saveDraft() {
      try {
        const { website: _honeypot, ...draft } = this.form;
        localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
      } catch {
        // Storage unavailable; the form still works for this visit.
      }
    },

    restoreDraft() {
      try {
        const saved = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? "null");
        if (saved && typeof saved === "object") {
          Object.assign(this.form, saved, { website: "" });
        }
      } catch {
        this.clearDraft();
      }
    },

    clearDraft() {
      try {
        localStorage.removeItem(DRAFT_KEY);
      } catch {
        // Nothing to clean up when storage is unavailable.
      }
    },
  }));
};

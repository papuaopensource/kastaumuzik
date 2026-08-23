/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  /**
   * Origin of the Django API. Local fallback only; in production the Worker
   * variable of the same name wins. Not prefixed with PUBLIC_, so it stays out
   * of the client bundle.
   */
  readonly API_ORIGIN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

/** Worker-scoped variables, available only in the on-demand route. */
declare module "cloudflare:workers" {
  export const env: {
    API_ORIGIN?: string;
  };
}

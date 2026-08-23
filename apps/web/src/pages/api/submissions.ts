/**
 * Forwards a submitted recording to the Django API.
 *
 * The only route on the site that runs per request, so the browser posts to its
 * own origin. Django owns validation; this passes its verdict back unchanged.
 */

// Worker-scoped vars. `Astro.locals.runtime.env` was removed in Astro 6.
import { env } from "cloudflare:workers";

import type { APIRoute } from "astro";

export const prerender = false;

/** Fields the form is allowed to send. Anything else is dropped. */
const ALLOWED_FIELDS = [
  "youtube_url",
  "title",
  "performer",
  "description",
  "website",
] as const;

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

export const POST: APIRoute = async ({ request }) => {
  // Set as a Worker variable in production; .env is the local fallback.
  const apiOrigin = (
    env.API_ORIGIN ??
    import.meta.env.API_ORIGIN ??
    ""
  ).replace(/\/$/, "");

  if (!apiOrigin) {
    console.error("API_ORIGIN is not configured; cannot forward submission.");
    return json(
      { detail: "Pengiriman usulan sedang tidak tersedia. Coba lagi nanti." },
      503,
    );
  }

  let submitted: Record<string, unknown>;
  try {
    const contentType = request.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      submitted = await request.json();
    } else {
      // Lets the form keep working if scripts fail to load.
      submitted = Object.fromEntries(await request.formData());
    }
  } catch {
    return json({ detail: "Isi permintaan tidak terbaca." }, 400);
  }

  const payload: Record<string, unknown> = {};
  for (const field of ALLOWED_FIELDS) {
    if (field in submitted) payload[field] = submitted[field];
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiOrigin}/api/v1/submissions/`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        // So Django throttles the visitor rather than the Worker.
        "x-forwarded-for":
          request.headers.get("cf-connecting-ip") ??
          request.headers.get("x-forwarded-for") ??
          "",
      },
      body: JSON.stringify(payload),
    });
  } catch (cause) {
    console.error("Submission could not reach the API:", cause);
    return json(
      { detail: "Tidak dapat menghubungi server. Coba lagi sebentar lagi." },
      502,
    );
  }

  const text = await upstream.text();
  return new Response(text || "{}", {
    status: upstream.status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
};

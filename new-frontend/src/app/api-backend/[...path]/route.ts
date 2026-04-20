import { NextRequest, NextResponse } from "next/server";

/**
 * Dev proxy to the Python API. Next.js URL rewrites can mishandle multipart uploads
 * (file + boundary), which surfaces as 500 from the dev server. This handler forwards
 * the raw body and Content-Type so PDF/DOCX analysis works reliably.
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const backendBase = (process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

type RouteCtx = { params: Promise<{ path: string[] }> };

async function forwardToBackend(req: NextRequest, pathSegments: string[]) {
  const subpath = pathSegments.join("/");
  const target = `${backendBase}/${subpath}${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const accept = req.headers.get("accept");
  if (accept) headers.set("accept", accept);

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD" && req.method !== "OPTIONS") {
    init.body = await req.arrayBuffer();
  }

  const upstream = await fetch(target, init);

  const outHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      outHeaders.set(key, value);
    }
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: outHeaders,
  });
}

export async function GET(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return forwardToBackend(req, path);
}

export async function POST(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return forwardToBackend(req, path);
}

export async function OPTIONS(req: NextRequest, ctx: RouteCtx) {
  const { path } = await ctx.params;
  return forwardToBackend(req, path);
}

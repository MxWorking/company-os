import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const origin = process.env.BACKEND_ORIGIN?.replace(/\/$/, "");

  if (!origin) {
    return NextResponse.json(
      { connected: false, status: "not_configured" },
      { status: 503, headers: { "Cache-Control": "no-store" } }
    );
  }

  try {
    const response = await fetch(`${origin}/api/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) throw new Error("Backend returned an unsuccessful status");
    const data: unknown = await response.json();

    if (
      !data ||
      typeof data !== "object" ||
      !("status" in data) ||
      data.status !== "ok"
    ) {
      throw new Error("Unexpected backend response");
    }

    return NextResponse.json(
      { connected: true, status: "ok" },
      { headers: { "Cache-Control": "no-store" } }
    );
  } catch {
    return NextResponse.json(
      { connected: false, status: "unavailable" },
      { status: 503, headers: { "Cache-Control": "no-store" } }
    );
  }
}

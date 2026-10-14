import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function getBackendBaseUrl(): string {
  const rawUrl = process.env.APP_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return rawUrl.replace(/\/+$/, "");
}

export async function GET(req: NextRequest) {
  const backendBase = getBackendBaseUrl();
  const targetUrl = new URL("openapi.json", `${backendBase}/`);
  targetUrl.search = req.nextUrl.search;

  try {
    const res = await fetch(targetUrl.toString(), { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { detail: `Không thể kết nối openapi.json: ${String(error)}` },
      { status: 502 }
    );
  }
}

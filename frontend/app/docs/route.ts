import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function getBackendBaseUrl(): string {
  const rawUrl = process.env.APP_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return rawUrl.replace(/\/+$/, "");
}

export async function GET(req: NextRequest) {
  const backendBase = getBackendBaseUrl();
  const targetUrl = new URL("docs", `${backendBase}/`);
  targetUrl.search = req.nextUrl.search;

  try {
    const res = await fetch(targetUrl.toString(), { cache: "no-store" });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: {
        "Content-Type": "text/html; charset=utf-8",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { detail: `Không thể kết nối tài liệu Swagger Docs: ${String(error)}` },
      { status: 502 }
    );
  }
}

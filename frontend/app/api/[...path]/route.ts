import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * Lấy URL gốc của dịch vụ backend FastAPI nội bộ từ biến môi trường APP_URL (do Vercel Services binding tiêm vào).
 * Fallback sang NEXT_PUBLIC_API_URL hoặc localhost khi chạy môi trường dev cục bộ.
 */
function getBackendBaseUrl(): string {
  const rawUrl = process.env.APP_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  return rawUrl.replace(/\/+$/, "");
}

/**
 * Xử lý ủy quyền (proxy) các request từ client đến dịch vụ backend nội bộ qua Vercel Service Binding.
 */
async function handleProxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const backendBase = getBackendBaseUrl();
  const targetPath = `/api/${path.join("/")}`;
  
  // Dùng new URL() để ánh xạ chính xác đường dẫn đến dịch vụ backend
  const targetUrl = new URL(targetPath.replace(/^\//, ""), `${backendBase}/`);
  targetUrl.search = req.nextUrl.search;

  // Chuyển tiếp các headers (loại trừ host để tránh xung đột routing nội bộ)
  const forwardHeaders = new Headers();
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") {
      forwardHeaders.set(key, value);
    }
  });

  const fetchOptions: RequestInit = {
    method: req.method,
    headers: forwardHeaders,
    cache: "no-store",
  };

  // Đọc body cho các phương thức POST / PUT / PATCH / DELETE
  if (req.method !== "GET" && req.method !== "HEAD") {
    const contentType = req.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      fetchOptions.body = await req.text();
    } else {
      fetchOptions.body = await req.blob();
    }
  }

  try {
    const response = await fetch(targetUrl, fetchOptions);
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      responseHeaders.set(key, value);
    });

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error(`[Vercel Service Proxy Error] Không thể kết nối backend tại ${targetUrl.toString()}:`, error);
    return NextResponse.json(
      {
        detail: `Không thể kết nối đến dịch vụ backend nội bộ (APP_URL): ${String(error)}`,
      },
      { status: 502 }
    );
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
export const PUT = handleProxy;
export const DELETE = handleProxy;
export const PATCH = handleProxy;
export const HEAD = handleProxy;
export const OPTIONS = handleProxy;

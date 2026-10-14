// API Client kết nối với FastAPI Backend (Appota NextGen Enterprise Secure RAG)

export interface UserProfile {
  user_id: string;
  name: string;
  company: string;
  dept: string;
  role_level: number;
}

export interface SourceNodeInfo {
  title: string;
  file_id?: string;
  required_level?: number;
  required_dept?: string;
  score?: number;
  text_excerpt?: string;
}

export interface ChatResponse {
  status: string;
  query: string;
  response: string;
  user: UserProfile;
  sources: string[];
  source_details?: SourceNodeInfo[];
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  is_ready: boolean;
  config: {
    llm_model: string;
    embedding_model: string;
    enable_hybrid: boolean;
    sparse_model: string;
    enable_rerank: boolean;
    rerank_model: string;
    retrieval_top_k: number;
    rerank_top_k: number;
  };
}

export interface IngestResponse {
  status: string;
  message: string;
  documents_count?: number;
}

/**
 * Lấy URL đích để gọi API:
 * - Phía Server (Vercel Serverless Functions / SSR): Dùng biến APP_URL được Vercel Service Binding tiêm vào runtime.
 * - Phía Client (Browser): Dùng relative path để đi qua Next.js API route handler, hoặc NEXT_PUBLIC_API_URL nếu được chỉ định.
 */
function getTargetUrl(endpoint: string): string {
  const cleanEndpoint = endpoint.replace(/^\/+/, "");
  if (typeof window === "undefined") {
    const rawBase = process.env.APP_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const base = rawBase.endsWith("/") ? rawBase : `${rawBase}/`;
    return new URL(cleanEndpoint, base).toString();
  }
  const publicBase = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, "");
  return publicBase ? new URL(cleanEndpoint, `${publicBase}/`).toString() : `/${cleanEndpoint}`;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = getTargetUrl(endpoint);
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `Lỗi máy chủ (${res.status})`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          errorMsg = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // bỏ qua nếu response không phải JSON
      }
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof Error) {
      throw err;
    }
    throw new Error(String(err));
  }
}

export const ragApi = {
  // Lấy trạng thái hệ thống
  getHealth: (): Promise<HealthResponse> => {
    return request<HealthResponse>("/api/health");
  },

  // Lấy danh sách toàn bộ người dùng để phân quyền RBAC
  getUsers: (): Promise<UserProfile[]> => {
    return request<UserProfile[]>("/api/users");
  },

  // Đăng nhập / Kiểm tra mã định danh User ID
  login: (userId: string): Promise<{ status: string; user: UserProfile }> => {
    return request<{ status: string; user: UserProfile }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    });
  },

  // Gửi truy vấn RAG có phân quyền bảo mật & FlashRank Reranker
  chat: (userId: string, query: string): Promise<ChatResponse> => {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, query }),
    });
  },

  // Yêu cầu tái lập chỉ mục (Re-ingest)
  ingest: (): Promise<IngestResponse> => {
    return request<IngestResponse>("/api/ingest", {
      method: "POST",
    });
  },
};

import os
import sys

# Tối ưu bộ nhớ RAM cho môi trường Cloud hạn chế (Render Free Tier 512MB)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# Cấu hình encoding UTF-8 để hỗ trợ tiếng Việt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from llama_index.core import Settings, VectorStoreIndex

from src.config import Config
from src.models import setup_global_models
from src.user_manager import AuthManager
from src.vector_store import Qdrant_Manager
from src.rag_engine import SecureRAGEngine
from src.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và dọn dẹp tài nguyên của ứng dụng FastAPI."""
    if os.getenv("TESTING", "").lower() in ("1", "true"):
        setup_global_models()
        app.state.is_ready = True
        yield
        return

    print("[Server Startup] Đang chuẩn bị hệ thống RAG...")
    
    # 1. Thiết lập mô hình
    setup_global_models()
    
    # 2. Khởi tạo Qdrant Vector Store
    vector_store = Qdrant_Manager()
    app.state.vector_store = vector_store

    # 3. Kết nối hoặc tự động lập chỉ mục Index trong Qdrant
    collection_name = getattr(Config, "COLLECTION_NAME", "rag_collection")
    try:
        need_reingest = False
        if vector_store.client.collection_exists(collection_name):
            coll_info = vector_store.client.get_collection(collection_name)
            has_sparse = bool(getattr(coll_info.config.params, "sparse_vectors", None))
            
            # Kiểm tra vector dimension của dense vector
            vectors_param = getattr(coll_info.config.params, "vectors", None)
            current_dim = None
            if hasattr(vectors_param, "size"):
                current_dim = vectors_param.size
            elif isinstance(vectors_param, dict) and "text-dense" in vectors_param:
                current_dim = getattr(vectors_param["text-dense"], "size", None)

            expected_dim = 768
            points_count = getattr(coll_info, "points_count", 0) or 0
            if points_count == 0:
                print(f"[Qdrant] Collection '{collection_name}' đang có 0 điểm dữ liệu (chưa nạp hoặc deploy mới). Cần tiến hành nạp tài liệu...")
                need_reingest = True
            elif current_dim is not None and current_dim != expected_dim:
                print(f"[Qdrant] Dimension cấu hình ({current_dim}) không khớp {expected_dim} (GoogleGenAIEmbedding). Cần tái lập chỉ mục...")
                need_reingest = True
            elif getattr(Config, "ENABLE_HYBRID", True) and not has_sparse:
                print(f"[Qdrant] Collection '{collection_name}' chưa có cấu hình Sparse Vector. Cần tái cấu trúc Hybrid...")
                need_reingest = True
            else:
                # Kiểm tra dimension thực tế của các điểm dữ liệu đã lưu trữ
                try:
                    sample_pts, _ = vector_store.client.scroll(collection_name, limit=1, with_vectors=True)
                    if sample_pts and sample_pts[0].vector is not None:
                        vec_val = sample_pts[0].vector
                        dense_vec = vec_val.get("text-dense") if isinstance(vec_val, dict) else vec_val
                        if dense_vec is not None and len(dense_vec) != expected_dim:
                            print(f"[Qdrant] Vector thực tế trên đĩa ({len(dense_vec)}) khác {expected_dim}. Cần tái lập chỉ mục...")
                            need_reingest = True
                except Exception:
                    pass

            if not need_reingest:
                print(f"[Qdrant] Đã phát hiện collection '{collection_name}' (Hybrid Ready, dim={expected_dim}). Đang kết nối trực tiếp...")
                index = VectorStoreIndex.from_vector_store(
                    vector_store=vector_store.vector_store,
                    embed_model=Settings.embed_model
                )
        else:
            need_reingest = True

        if need_reingest:
            print(f"[Qdrant] Đang tiến hành quét data/ và tái lập chỉ mục chuẩn Hybrid (Dense 768 + Sparse BM25)...")
            index = vector_store.ingest_data_and_create_index(show_progress=False, recreate_collection=True)
    except Exception as e:
        print(f"[Qdrant] Lỗi kiểm tra collection ({e}). Đang tái lập chỉ mục...")
        index = vector_store.ingest_data_and_create_index(show_progress=False, recreate_collection=True)

    # 4. Khởi tạo Engine bảo mật & Auth
    rag_engine = SecureRAGEngine(index)
    auth_manager = AuthManager()

    app.state.rag_engine = rag_engine
    app.state.auth_manager = auth_manager
    app.state.is_ready = True
    
    # Giải phóng bộ nhớ đệm (Garbage Collection) giúp giảm RAM tiêu thụ trên Render
    import gc
    gc.collect()

    print("[Server Startup] ✅ Hệ thống Enterprise Secure RAG đã sẵn sàng phục vụ API!")
    
    yield
    
    print("[Server Shutdown] Đang dừng dịch vụ...")

# Khởi tạo FastAPI app
app = FastAPI(
    title="Appota NextGen Enterprise Secure RAG API",
    version="1.0.0",
    description="Hệ thống RAG Doanh Nghiệp tích hợp Phân quyền Bảo mật (RBAC), Hybrid Search (Dense + BM25) và FlashRank Reranker.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Kích hoạt CORS Middleware để phục vụ việc tích hợp giao diện Frontend (React, Vue, HTML,...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đảm bảo thư mục static tồn tại để chuẩn bị triển khai giao diện UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Đăng ký API router
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse, summary="Trang chủ / API Portal")
def root_portal():
    """Trang thông tin tổng quan về API và hướng dẫn sử dụng."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    # Trang giới thiệu mặc định khi chưa triển khai index.html
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Appota NextGen Secure RAG API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px 20px; display: flex; justify-content: center; }
            .card { background: #1e293b; border-radius: 12px; padding: 32px; max-width: 650px; width: 100%; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
            h1 { color: #38bdf8; font-size: 24px; margin-top: 0; }
            p { color: #94a3b8; line-height: 1.6; }
            .badge { display: inline-block; background: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-bottom: 16px; }
            .features { margin: 20px 0; padding-left: 20px; color: #cbd5e1; }
            .features li { margin-bottom: 8px; }
            .btn { display: inline-block; background: #2563eb; color: white; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 500; margin-right: 12px; transition: background 0.2s; }
            .btn:hover { background: #1d4ed8; }
            .btn-outline { background: transparent; border: 1px solid #475569; color: #e2e8f0; }
            .btn-outline:hover { background: #334155; }
        </style>
    </head>
    <body>
        <div class="card">
            <span class="badge">🚀 API READY</span>
            <h1>Appota NextGen Enterprise Secure RAG</h1>
            <p>Hệ thống RAG thông minh tích hợp phân quyền bảo mật (RBAC), tìm kiếm kết hợp Hybrid Search (Dense + BM25) và FlashRank Reranker đã sẵn sàng phục vụ.</p>
            <ul class="features">
                <li><b>Bảo mật RBAC:</b> Lọc cứng đa tầng theo cấp bậc và phòng ban</li>
                <li><b>Hybrid Search:</b> Dense Vector E5-Large + Sparse BM25</li>
                <li><b>FlashRank:</b> Tái xếp hạng câu trả lời chính xác vượt trội</li>
                <li><b>Chunking:</b> Phân tích giữ nguyên cấu trúc Markdown Headers & Tables</li>
            </ul>
            <div style="margin-top: 28px;">
                <a href="/docs" class="btn">Xem tài liệu Swagger API (/docs)</a>
                <a href="/api/health" class="btn btn-outline">Kiểm tra Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



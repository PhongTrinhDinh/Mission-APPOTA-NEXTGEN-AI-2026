import torch
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.config import Config
from src.user_manager import AuthManager
from src.rag_engine import SecureRAGEngine
from src.vector_store import Qdrant_Manager
from src.api.schemas import (
    LoginRequest,
    LoginResponse,
    UserProfile,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestResponse,
    SourceNodeInfo,
)
from src.api.dependencies import get_auth_manager, get_rag_engine, get_vector_store

router = APIRouter(prefix="/api", tags=["Enterprise Secure RAG"])

@router.get("/health", response_model=HealthResponse, summary="Kiểm tra trạng thái hệ thống")
def health_check(
    rag_engine: SecureRAGEngine = Depends(get_rag_engine)
) -> HealthResponse:
    """Trả về trạng thái hoạt động của RAG Engine, mô hình và cấu hình hệ thống."""
    device_str = "Local GPU (CUDA)" if torch.cuda.is_available() else "Local CPU"
    return HealthResponse(
        status="ok",
        app_name="Appota NextGen Enterprise Secure RAG API",
        version="1.0.0",
        is_ready=rag_engine is not None,
        config={
            "llm_model": Config.LLM_MODEL,
            "embedding_model": f"{Config.EMBEDDING_MODEL} ({device_str})",
            "enable_hybrid": Config.ENABLE_HYBRID,
            "sparse_model": Config.SPARSE_MODEL,
            "enable_rerank": Config.ENABLE_RERANK,
            "rerank_model": Config.RERANK_MODEL,
            "retrieval_top_k": Config.RETRIEVAL_TOP_K,
            "rerank_top_k": Config.RERANK_TOP_K,
        }
    )

@router.get("/users", response_model=List[UserProfile], summary="Danh sách người dùng có thể đăng nhập")
def list_users(
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> List[UserProfile]:
    """Lấy danh sách toàn bộ nhân viên/vai trò trong hệ thống (dùng để chọn tài khoản trên giao diện)."""
    return [UserProfile(**u) for u in auth_manager.users.values()]

@router.post("/auth/login", response_model=LoginResponse, summary="Đăng nhập tài khoản nhân viên")
def login(
    request: LoginRequest,
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> LoginResponse:
    """Xác thực mã định danh User ID và trả về hồ sơ phân quyền nhân viên."""
    try:
        user_dict = auth_manager.login(request.user_id.strip())
        return LoginResponse(
            status="success",
            user=UserProfile(**user_dict)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy tài khoản với User ID: '{request.user_id}'"
        )

@router.post("/chat", response_model=ChatResponse, summary="Gửi câu hỏi tra cứu chính sách (kèm bảo mật RBAC)")
def chat(
    request: ChatRequest,
    auth_manager: AuthManager = Depends(get_auth_manager),
    rag_engine: SecureRAGEngine = Depends(get_rag_engine),
) -> ChatResponse:
    """
    Truy vấn hệ thống RAG doanh nghiệp:
    1. Kiểm tra tài khoản người dùng và xác định vai trò/cấp bậc bảo mật.
    2. Tự động áp dụng Hard Filters (RBAC) tương thích cấp bậc và phòng ban.
    3. Thực thi Hybrid Search (Dense + Sparse BM25) trong Qdrant.
    4. FlashRank Reranker chấm điểm và lọc top câu trả lời chính xác nhất.
    """
    user_id = request.user_id.strip()
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung câu hỏi không được để trống."
        )

    # 1. Xác thực user
    try:
        user_profile = auth_manager.login(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User ID '{user_id}' không hợp lệ hoặc chưa được cấp quyền."
        )

    # 2. Thực hiện chat qua SecureRAGEngine
    try:
        sources: List[str] = []
        source_details: List[SourceNodeInfo] = []
        answer = ""

        if hasattr(rag_engine, "query_with_sources"):
            engine_resp = rag_engine.query_with_sources(query, user_profile)
            answer = getattr(engine_resp, "response", str(engine_resp))
            if hasattr(engine_resp, "source_nodes") and engine_resp.source_nodes:
                for node_with_score in engine_resp.source_nodes:
                    node = getattr(node_with_score, "node", node_with_score)
                    meta = getattr(node, "metadata", {})
                    score = getattr(node_with_score, "score", None)
                    doc_title = meta.get("title", meta.get("file_name", "Tài liệu"))
                    file_id = meta.get("file_id", None)
                    req_level = meta.get("required_level", 1)
                    req_dept = meta.get("required_dept", "ALL")
                    
                    text_excerpt = None
                    if hasattr(node, "get_text"):
                        text_excerpt = node.get_text()[:300].strip()
                    elif hasattr(node, "text"):
                        text_excerpt = str(node.text)[:300].strip()

                    sources.append(doc_title)
                    source_details.append(SourceNodeInfo(
                        title=doc_title,
                        file_id=file_id,
                        required_level=req_level,
                        required_dept=req_dept,
                        score=round(score, 4) if score is not None else None,
                        text_excerpt=text_excerpt
                    ))
                # Loại bỏ tiêu đề trùng lặp giữ nguyên thứ tự
                sources = list(dict.fromkeys(sources))
        else:
            answer = rag_engine.chat(query, user_profile)

        # Nếu câu trả lời chứa thông tin lỗi từ chat engine
        if isinstance(answer, str) and answer.startswith("Đã xảy ra lỗi khi truy vấn:"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=answer
            )

        return ChatResponse(
            status="success",
            query=query,
            response=str(answer),
            user=UserProfile(**user_profile),
            sources=sources,
            source_details=source_details if source_details else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý truy vấn AI: {str(e)}"
        )

@router.post("/ingest", response_model=IngestResponse, summary="Tải và tái lập chỉ mục dữ liệu")
def ingest_documents(
    request: Request,
    vector_store: Qdrant_Manager = Depends(get_vector_store)
) -> IngestResponse:
    """Tái quét thư mục tài liệu markdown và cập nhật chỉ mục vào Qdrant."""
    try:
        index = vector_store.ingest_data_and_create_index(show_progress=False, recreate_collection=True)
        # Đồng bộ và cập nhật lại SecureRAGEngine với index mới trong bộ nhớ ứng dụng
        request.app.state.rag_engine = SecureRAGEngine(index)
        return IngestResponse(
            status="success",
            message="Đã tái lập chỉ mục Hybrid Search và cập nhật RAG Engine thành công."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi nạp dữ liệu: {str(e)}"
        )

from fastapi import Request, HTTPException, status
from src.user_manager import AuthManager
from src.rag_engine import SecureRAGEngine
from src.vector_store import Qdrant_Manager

def get_auth_manager(request: Request) -> AuthManager:
    """Dependency cung cấp AuthManager từ application state."""
    auth_manager = getattr(request.app.state, "auth_manager", None)
    if auth_manager is None:
        # Fallback tạo mới nếu chưa có trong state
        auth_manager = AuthManager()
        request.app.state.auth_manager = auth_manager
    return auth_manager

def get_rag_engine(request: Request) -> SecureRAGEngine:
    """Dependency cung cấp SecureRAGEngine từ application state."""
    rag_engine = getattr(request.app.state, "rag_engine", None)
    if rag_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hệ thống RAG đang khởi động hoặc chưa sẵn sàng. Vui lòng thử lại sau ít giây."
        )
    return rag_engine

def get_vector_store(request: Request) -> Qdrant_Manager:
    """Dependency cung cấp Qdrant_Manager từ application state."""
    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        vector_store = Qdrant_Manager()
        request.app.state.vector_store = vector_store
    return vector_store

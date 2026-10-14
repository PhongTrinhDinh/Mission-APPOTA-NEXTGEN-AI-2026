import os
from dotenv import load_dotenv

# Nạp biến môi trường từ .env
load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    if not GOOGLE_API_KEY and os.getenv("TESTING", "").lower() not in ("1", "true"):
        raise ValueError("[!] Vui lòng cung cấp GOOGLE_API_KEY (hoặc GEMINI_API_KEY) trong file .env")

    
    # Cấu hình LLM & Embedding Model
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    
    # Tham số sinh văn bản & ngữ cảnh
    CONTEXT_WINDOW = 4096
    MAX_NEW_TOKENS = 512
    TEMPERATURE = 0.1
    
    # Cấu hình lưu trữ Qdrant Vector DB
    QDRANT_LOCATION = "./qdrant_db"
    COLLECTION_NAME = "rag_collection"
    
    # Cấu hình lưu trữ Model Local
    LOCAL_MODEL_DIR = "./local_model"
    
    # Dữ liệu tài liệu & Người dùng
    DATA_DIR = os.getenv("DATA_DIR", "data")
    DOCS_DIR = os.getenv("DOCS_DIR", "data")
    USERS_FILE = os.getenv("USERS_FILE", "users.json")
    SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))

    # Advanced RAG: Hybrid Search (Dense Vector + Sparse BM25)
    ENABLE_HYBRID = os.getenv("ENABLE_HYBRID", "true").lower() in ("true", "1")
    SPARSE_MODEL = os.getenv("SPARSE_MODEL", "Qdrant/bm25")

    # Advanced RAG: FlashRank Reranker
    ENABLE_RERANK = os.getenv("ENABLE_RERANK", "true").lower() in ("true", "1")
    RERANK_MODEL = os.getenv("RERANK_MODEL", "ms-marco-MiniLM-L-12-v2")
    RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "15"))
    RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))

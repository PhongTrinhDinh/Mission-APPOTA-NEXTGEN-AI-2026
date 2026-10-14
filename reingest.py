import sys
from pathlib import Path

# Cấu hình UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.models import setup_global_models
from src.vector_store import Qdrant_Manager

def run():
    print("[1/3] Khởi tạo mô hình (Google GenAI Embedding & LLM)...")
    setup_global_models()

    print("[2/3] Khởi tạo Qdrant Manager và tái lập chỉ mục Hybrid...")
    qm = Qdrant_Manager()
    index = qm.ingest_data_and_create_index(show_progress=True, recreate_collection=True)

    print("[3/3] Kiểm tra cấu trúc Collection sau khi tái lập chỉ mục:")
    coll = qm.client.get_collection("rag_collection")
    print(f"  • Points count: {coll.points_count}")
    print(f"  • Dense Vectors: {coll.config.params.vectors}")
    print(f"  • Sparse Vectors (BM25): {coll.config.params.sparse_vectors}")
    print("\n✅ TÁI LẬP CHỈ MỤC CHUẨN HYBRID THÀNH CÔNG!")
    qm.client.close()

if __name__ == "__main__":
    run()

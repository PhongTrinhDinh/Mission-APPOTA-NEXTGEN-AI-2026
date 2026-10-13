from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from src.config import Config
import os
import re
import yaml

class Qdrant_Manager:
    def __init__(
        self,
        location: str = None,
        collection_name: str = None,
        client = None,
        enable_hybrid: bool = None,
        fastembed_sparse_model: str = None
    ):
        if client is not None:
            self.client = client
        else:
            db_path = location or getattr(Config, "QDRANT_LOCATION", "./qdrant_db")
            # Dọn dẹp lock file cũ nếu có (thường do git commit hoặc crash từ phiên trước)
            lock_file = os.path.join(db_path, ".lock")
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
            self.client = QdrantClient(path=db_path)

        coll_name = collection_name or getattr(Config, "COLLECTION_NAME", "rag_collection")
        is_hybrid = enable_hybrid if enable_hybrid is not None else getattr(Config, "ENABLE_HYBRID", True)
        sparse_model = fastembed_sparse_model or getattr(Config, "SPARSE_MODEL", "Qdrant/bm25")

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=coll_name,
            enable_hybrid=is_hybrid,
            fastembed_sparse_model=sparse_model if is_hybrid else None
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def _parse_markdown_with_yaml(self, file_path: str) -> Document:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dùng Regex hỗ trợ cả Windows (\r\n) và Linux (\n) để tách block YAML giữa --- và ---
        match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n(.*)', content, re.DOTALL)
        if match:
            yaml_str = match.group(1)
            body_text = match.group(2).strip()
            try:
                metadata = yaml.safe_load(yaml_str)
                
                # CHUẨN HÓA METADATA ĐỂ PHÂN QUYỀN (Giải quyết xung đột thứ bậc & phòng ban)
                doc_id = metadata.get("id", "")
                flat_metadata = {
                    "file_id": doc_id,
                    "title": metadata.get("title", ""),
                }
                
                access_control = metadata.get("access_control", {})
                clearance = access_control.get("clearance_level", metadata.get("clearance_level", "LEVEL_1"))
                level_match = re.search(r'\d+', str(clearance))
                required_level = int(level_match.group()) if level_match else (4 if doc_id.startswith("CONF-HR") else 1)
                flat_metadata["required_level"] = required_level
                
                override_scope = str(metadata.get("override_scope", "")).upper()
                scope = str(metadata.get("scope", "")).upper()
                cls_str = str(access_control.get("classification", metadata.get("classification", "PUBLIC"))).upper()
                
                dept = "ALL"
                if "HR_ONLY" in cls_str or doc_id.startswith("CONF-HR"):
                    dept = "HR"
                elif "SALES_ONLY" in cls_str or "SALES" in doc_id or "KINH DOANH" in override_scope or "SALES" in override_scope:
                    dept = "Sales"
                elif "ENG_ONLY" in cls_str or "-ENG-" in doc_id or "KỸ THUẬT" in override_scope or "ENGINEERING" in override_scope:
                    dept = "Engineering"
                
                flat_metadata["required_dept"] = dept
                return Document(text=body_text, metadata=flat_metadata)
            except Exception as e:
                print(f"[!] Lỗi parse YAML tại file {file_path}: {e}")
                
        # Trả về document thường nếu không có YAML
        return Document(text=content, metadata={"required_level": 1, "required_dept": "ALL"})

    def recreate_hybrid_collection(self, collection_name: str = None):
        """Xóa collection cũ và khởi tạo lại collection với cấu trúc Hybrid Search (Dense + Sparse BM25)."""
        coll_name = collection_name or getattr(Config, "COLLECTION_NAME", "rag_collection")
        try:
            if self.client.collection_exists(coll_name):
                print(f"[Vector Store] Xóa collection cũ '{coll_name}' để tái cấu trúc...")
                self.client.delete_collection(coll_name)
        except Exception as e:
            print(f"[Vector Store] Cảnh báo khi xóa collection: {e}")

        is_hybrid = getattr(Config, "ENABLE_HYBRID", True)
        sparse_model = getattr(Config, "SPARSE_MODEL", "Qdrant/bm25")
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=coll_name,
            enable_hybrid=is_hybrid,
            fastembed_sparse_model=sparse_model if is_hybrid else None
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def ingest_data_and_create_index(
        self,
        docs_dir: str = None,
        show_progress: bool = True,
        recreate_collection: bool = False
    ) -> VectorStoreIndex:
        if recreate_collection:
            self.recreate_hybrid_collection()

        target_dir = docs_dir or getattr(Config, "DOCS_DIR", getattr(Config, "DATA_DIR", "data"))
        print(f"[Vector Store] Reading data from '{target_dir}'...")
        documents = []
        if os.path.exists(target_dir):
            for filename in sorted(os.listdir(target_dir)):
                if filename.endswith(".md"):
                    file_path = os.path.join(target_dir, filename)
                    doc = self._parse_markdown_with_yaml(file_path)
                    documents.append(doc)
                
        print(f"[Vector Store] Đã tải {len(documents)} tài liệu.")
        print("[Vector Store] Đang tạo Embeddings và lập chỉ mục Hybrid (Dense + Sparse BM25)...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=self.storage_context,
            show_progress=show_progress
        )
        return index
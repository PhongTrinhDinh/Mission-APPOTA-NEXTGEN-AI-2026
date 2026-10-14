from src.config import Config
from src.reranker import FlashRankRerank
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilter, MetadataFilters, FilterOperator, FilterCondition

class SecureRAGEngine:
    def __init__(self, index, reranker=None):
        self.index = index
        if reranker is not None:
            self.reranker = reranker
        elif getattr(Config, "ENABLE_RERANK", True):
            self.reranker = FlashRankRerank(
                model_name=getattr(Config, "RERANK_MODEL", "ms-marco-MiniLM-L-12-v2"),
                top_n=getattr(Config, "RERANK_TOP_K", getattr(Config, "SIMILARITY_TOP_K", 5)),
                cache_dir=getattr(Config, "LOCAL_MODEL_DIR", "./local_model")
            )
        else:
            self.reranker = None

    def build_hard_filters(self, user_context: dict) -> MetadataFilters:
        """Xây dựng bộ lọc cứng (Hard filter) để gửi xuống Qdrant DB"""
        user_level = user_context.get("role_level", 1)
        user_dept = user_context.get("dept", "")

        # ĐIỀU KIỆN 1: Bắt buộc Level của user phải LỚN HƠN HOẶC BẰNG Level của Document
        level_filter = MetadataFilter(
            key="required_level", 
            value=user_level, 
            operator=FilterOperator.LTE # LTE = Less Than or Equal (Doc Level <= User Level)
        )

        # ĐIỀU KIỆN 2: Xử lý phòng ban & Xung đột thứ bậc (C-Level được xem chéo phòng ban)
        if user_level >= 4:
            # Sếp lớn (BOD): Chỉ cần thỏa mãn level_filter ở trên, không bị giới hạn phòng ban.
            filters = MetadataFilters(
                filters=[level_filter], 
                condition=FilterCondition.AND
            )
        else:
            # Nhân viên/Quản lý cấp trung: Phải đúng phòng ban HOẶC tài liệu là ALL (public)
            dept_exact = ExactMatchFilter(key="required_dept", value=user_dept)
            dept_all = ExactMatchFilter(key="required_dept", value="ALL")
            
            dept_filters = MetadataFilters(
                filters=[dept_exact, dept_all],
                condition=FilterCondition.OR
            )
            
            # Gộp Điều kiện 1 VÀ Điều kiện 2
            filters = MetadataFilters(
                filters=[level_filter, dept_filters],
                condition=FilterCondition.AND
            )
            
        return filters

    def query_with_sources(self, user_query: str, user_context: dict):
        """Thực thi truy vấn RAG có lọc bảo mật và trả về toàn bộ đối tượng phản hồi kèm source_nodes."""
        security_filters = self.build_hard_filters(user_context)
        
        # Thiết lập tham số truy vấn Hybrid Search và Reranker
        retrieval_k = getattr(Config, "RETRIEVAL_TOP_K", 15) if self.reranker else getattr(Config, "SIMILARITY_TOP_K", 5)

        engine_kwargs = {
            "similarity_top_k": retrieval_k,
            "filters": security_filters
        }

        # Kích hoạt Hybrid Search nếu cấu hình bật
        if getattr(Config, "ENABLE_HYBRID", True):
            engine_kwargs["vector_store_query_mode"] = "hybrid"

        # Kích hoạt FlashRank Reranker
        if self.reranker is not None:
            engine_kwargs["node_postprocessors"] = [self.reranker]

        try:
            query_engine = self.index.as_query_engine(**engine_kwargs)
        except TypeError:
            # Fallback nếu index mock không hỗ trợ tham số vector_store_query_mode
            engine_kwargs.pop("vector_store_query_mode", None)
            query_engine = self.index.as_query_engine(**engine_kwargs)

        try:
            response = query_engine.query(user_query)
        except Exception as e:
            if "Sparse vector" in str(e) or "text-sparse-new" in str(e):
                print(f"[RAG Engine] Cảnh báo ({e}). Tự động fallback về Dense Vector...")
                engine_kwargs.pop("vector_store_query_mode", None)
                fallback_engine = self.index.as_query_engine(**engine_kwargs)
                response = fallback_engine.query(user_query)
            else:
                raise

        # Xử lý trường hợp LlamaIndex trả về "Empty Response" hoặc chuỗi rỗng
        resp_text = getattr(response, "response", "")
        if not resp_text or resp_text.strip() == "Empty Response":
            user_dept = user_context.get("dept", "Chưa xác định")
            user_level = user_context.get("role_level", 1)
            response.response = (
                f"🔒 **Không tìm thấy thông tin phù hợp trong phạm vi quyền hạn của bạn.**\n\n"
                f"- **Tài khoản:** Phòng ban `{user_dept}` | Cấp bậc: `Level {user_level}`\n"
                f"- **Lý do:** Nội dung câu hỏi có thể thuộc tài liệu mật (yêu cầu cấp bậc cao hơn), "
                f"thuộc phòng ban khác (bị cô lập bởi chính sách bảo mật RBAC), "
                f"hoặc thông tin chưa tồn tại trong kho quy chế của doanh nghiệp."
            )

        return response

    def chat(self, user_query: str, user_context: dict) -> str:
        """Phương thức chat trả về chuỗi câu trả lời (duy trì tương thích ngược)."""
        try:
            response = self.query_with_sources(user_query, user_context)
            if hasattr(response, "source_nodes") and response.source_nodes:
                sources = [node.metadata.get("title", "Unknown") for node in response.source_nodes]
                print(f"🔒 [Hệ thống] Đã trích xuất & Rerank thông tin từ: {list(set(sources))}")
            
            return getattr(response, "response", str(response))
        except Exception as e:
            return f"Đã xảy ra lỗi khi truy vấn: {e}"
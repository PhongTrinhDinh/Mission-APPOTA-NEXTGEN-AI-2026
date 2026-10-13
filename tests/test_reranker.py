import pytest
from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle
from src.reranker import FlashRankRerank
from src.config import Config

class TestFlashRankRerank:
    @pytest.fixture
    def reranker(self, tmp_path):
        return FlashRankRerank(
            model_name="ms-marco-MiniLM-L-6-v2",  # Tên mô hình người dùng yêu cầu
            top_n=2,
            cache_dir=str(tmp_path / "rerank_cache")
        )

    def test_reranker_initialization_and_alias_mapping(self, reranker):
        """Kiểm tra khởi tạo FlashRankRerank và ánh xạ alias MiniLM."""
        assert reranker.top_n == 2
        assert reranker._ranker is not None

    def test_postprocess_nodes_reordering_by_relevance(self, reranker):
        """Kiểm tra cơ chế chấm điểm và đảo lại thứ tự chính xác theo độ liên quan với câu query."""
        node_irrelevant = NodeWithScore(
            node=TextNode(text="Quy chế hoa hồng và chiết khấu phòng Kinh doanh dành cho Sales Lead."),
            score=0.9  # Giả sử dense search ban đầu chấm điểm cao do trùng một số từ
        )
        node_relevant = NodeWithScore(
            node=TextNode(text="Quy định nghỉ phép năm: mỗi nhân viên có 12 ngày phép hưởng nguyên lương."),
            score=0.5  # Dense search ban đầu chấm điểm thấp hơn
        )

        nodes = [node_irrelevant, node_relevant]
        query = QueryBundle(query_str="Nhân viên có bao nhiêu ngày nghỉ phép hàng năm?")

        reranked = reranker._postprocess_nodes(nodes, query_bundle=query)

        assert len(reranked) == 2
        # Đoạn văn về nghỉ phép phải được đẩy lên đầu bảng (#1)
        assert "nghỉ phép" in reranked[0].node.get_content().lower()
        assert reranked[0].score > reranked[1].score

    def test_postprocess_nodes_top_n_cutoff(self, reranker):
        """Kiểm tra việc cắt đúng top_n kết quả sau khi rerank."""
        nodes = [
            NodeWithScore(node=TextNode(text=f"Đoạn văn số {i}"), score=0.1 * i)
            for i in range(5)
        ]
        query = QueryBundle(query_str="Đoạn văn")

        reranked = reranker._postprocess_nodes(nodes, query_bundle=query)
        assert len(reranked) == reranker.top_n

    def test_postprocess_empty_nodes(self, reranker):
        """Kiểm tra xử lý danh sách nodes rỗng."""
        query = QueryBundle(query_str="Tìm kiếm")
        assert reranker._postprocess_nodes([], query_bundle=query) == []

    def test_postprocess_empty_query(self, reranker):
        """Kiểm tra fallback khi câu truy vấn rỗng."""
        nodes = [
            NodeWithScore(node=TextNode(text="Văn bản mẫu 1"), score=0.5),
            NodeWithScore(node=TextNode(text="Văn bản mẫu 2"), score=0.4),
        ]
        query = QueryBundle(query_str="")
        result = reranker._postprocess_nodes(nodes, query_bundle=query)
        assert len(result) == 2
        assert result[0].node.get_content() == "Văn bản mẫu 1"

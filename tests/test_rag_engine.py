import pytest
from unittest.mock import MagicMock
from llama_index.core.vector_stores import (
    ExactMatchFilter,
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition,
)
from src.rag_engine import SecureRAGEngine
from src.config import Config

class TestSecureRAGEngineFilters:
    @pytest.fixture
    def engine(self, mock_index):
        return SecureRAGEngine(index=mock_index)

    def test_c_level_user_filters_level_4(self, engine):
        """Kiểm tra người dùng cấp C-Level (Level 4): Không bị giới hạn phòng ban (xem chéo phòng ban)."""
        c_level_user = {
            "user_id": "U99",
            "name": "CEO",
            "dept": "BOD",
            "role_level": 4
        }
        filters = engine.build_hard_filters(c_level_user)

        assert isinstance(filters, MetadataFilters)
        assert filters.condition == FilterCondition.AND
        # Chỉ có 1 bộ lọc duy nhất: required_level <= 4
        assert len(filters.filters) == 1
        
        level_filter = filters.filters[0]
        assert isinstance(level_filter, MetadataFilter)
        assert level_filter.key == "required_level"
        assert level_filter.value == 4
        assert level_filter.operator == FilterOperator.LTE

    def test_c_level_user_filters_level_5(self, engine):
        """Kiểm tra người dùng cấp cao nhất (Level 5 - Chủ tịch HĐQT)."""
        chairman = {
            "user_id": "U100",
            "name": "Chairman",
            "dept": "BOD",
            "role_level": 5
        }
        filters = engine.build_hard_filters(chairman)
        assert len(filters.filters) == 1
        assert filters.filters[0].value == 5
        assert filters.filters[0].operator == FilterOperator.LTE

    def test_hr_manager_filters_level_3(self, engine):
        """Kiểm tra quản lý HR (Level 3): xem được HR và ALL, nhưng required_level <= 3."""
        hr_manager = {
            "user_id": "U01",
            "name": "Nguyễn Văn A",
            "dept": "HR",
            "role_level": 3
        }
        filters = engine.build_hard_filters(hr_manager)

        assert isinstance(filters, MetadataFilters)
        assert filters.condition == FilterCondition.AND
        assert len(filters.filters) == 2

        # Filter 1: Level LTE 3
        level_filter = filters.filters[0]
        assert level_filter.key == "required_level"
        assert level_filter.value == 3
        assert level_filter.operator == FilterOperator.LTE

        # Filter 2: Dept (HR OR ALL)
        dept_filters = filters.filters[1]
        assert isinstance(dept_filters, MetadataFilters)
        assert dept_filters.condition == FilterCondition.OR
        assert len(dept_filters.filters) == 2
        
        expected_values = {f.value for f in dept_filters.filters}
        assert expected_values == {"HR", "ALL"}
        for f in dept_filters.filters:
            assert f.key == "required_dept"

    def test_sales_staff_filters_level_1(self, engine):
        """Kiểm tra nhân viên Sales (Level 1): chỉ xem được Sales và ALL với Level <= 1."""
        sales_staff = {
            "user_id": "U02",
            "name": "Trần Thị B",
            "dept": "Sales",
            "role_level": 1
        }
        filters = engine.build_hard_filters(sales_staff)

        level_filter = filters.filters[0]
        assert level_filter.value == 1
        assert level_filter.operator == FilterOperator.LTE

        dept_filters = filters.filters[1]
        expected_values = {f.value for f in dept_filters.filters}
        assert expected_values == {"Sales", "ALL"}

    def test_engineering_staff_filters_level_1(self, engine):
        """Kiểm tra nhân viên Kỹ thuật (Level 1): chỉ xem được Engineering và ALL với Level <= 1."""
        eng_staff = {
            "user_id": "U03",
            "name": "Lê Văn C",
            "dept": "Engineering",
            "role_level": 1
        }
        filters = engine.build_hard_filters(eng_staff)

        dept_filters = filters.filters[1]
        expected_values = {f.value for f in dept_filters.filters}
        assert expected_values == {"Engineering", "ALL"}

    def test_fallback_when_context_missing_fields(self, engine):
        """Kiểm tra khi user context thiếu role_level hoặc dept thì gán giá trị an toàn mặc định."""
        empty_context = {}
        filters = engine.build_hard_filters(empty_context)

        # role_level mặc định là 1 (level thấp nhất)
        level_filter = filters.filters[0]
        assert level_filter.value == 1

        dept_filters = filters.filters[1]
        expected_values = {f.value for f in dept_filters.filters}
        assert expected_values == {"", "ALL"}

class TestSecureRAGEngineChat:
    def test_chat_successful_query_flow(self, mock_index, mock_query_engine):
        """Kiểm tra luồng chat gọi query_engine và trả về câu trả lời với Hybrid mode & Reranker."""
        mock_reranker = MagicMock()
        engine = SecureRAGEngine(index=mock_index, reranker=mock_reranker)
        user_context = {"role_level": 3, "dept": "HR"}

        response = engine.chat("Chính sách phúc lợi là gì?", user_context)

        # Kiểm tra as_query_engine được gọi với retrieval_k, filters, hybrid mode và reranker
        mock_index.as_query_engine.assert_called_once()
        call_kwargs = mock_index.as_query_engine.call_args[1]
        assert call_kwargs["similarity_top_k"] == Config.RETRIEVAL_TOP_K
        assert "filters" in call_kwargs
        assert call_kwargs.get("vector_store_query_mode") == "hybrid"
        assert call_kwargs.get("node_postprocessors") == [mock_reranker]

        # Kiểm tra gọi query
        mock_query_engine.query.assert_called_once_with("Chính sách phúc lợi là gì?")
        assert response == "Đây là câu trả lời thử nghiệm từ AI."

    def test_chat_without_reranker_fallback(self, mock_index, mock_query_engine):
        """Kiểm tra fallback khi tắt reranker thì similarity_top_k quay về Config.SIMILARITY_TOP_K."""
        engine = SecureRAGEngine(index=mock_index, reranker=False)
        engine.reranker = None
        user_context = {"role_level": 1, "dept": "Sales"}

        engine.chat("Tìm kiếm cơ bản", user_context)
        call_kwargs = mock_index.as_query_engine.call_args[1]
        assert call_kwargs["similarity_top_k"] == Config.SIMILARITY_TOP_K
        assert "node_postprocessors" not in call_kwargs

    def test_chat_exception_handling(self, mock_index):
        """Kiểm tra cơ chế bắt lỗi an toàn khi câu query gặp sự cố không làm crash chương trình."""
        bad_query_engine = MagicMock()
        bad_query_engine.query.side_effect = RuntimeError("Mất kết nối cơ sở dữ liệu Qdrant")
        mock_index.as_query_engine.return_value = bad_query_engine

        engine = SecureRAGEngine(index=mock_index)
        user_context = {"role_level": 1, "dept": "Sales"}

        result = engine.chat("Câu hỏi thử nghiệm", user_context)
        assert "Đã xảy ra lỗi khi truy vấn:" in result
        assert "Mất kết nối cơ sở dữ liệu Qdrant" in result

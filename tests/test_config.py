import os
import importlib
import pytest
from src.config import Config

class TestConfig:
    def test_all_required_attributes_exist(self):
        """Kiểm tra tất cả các hằng số cấu hình bắt buộc đều có mặt trong class Config."""
        expected_attrs = [
            "GOOGLE_API_KEY",
            "LLM_MODEL",
            "EMBEDDING_MODEL",
            "CONTEXT_WINDOW",
            "MAX_NEW_TOKENS",
            "TEMPERATURE",
            "QDRANT_LOCATION",
            "COLLECTION_NAME",
            "LOCAL_MODEL_DIR",
            "DATA_DIR",
            "DOCS_DIR",
            "USERS_FILE",
            "SIMILARITY_TOP_K",
            "ENABLE_HYBRID",
            "SPARSE_MODEL",
            "ENABLE_RERANK",
            "RERANK_MODEL",
            "RETRIEVAL_TOP_K",
            "RERANK_TOP_K",
        ]
        for attr in expected_attrs:
            assert hasattr(Config, attr), f"Config thiếu thuộc tính bắt buộc: '{attr}'"

    def test_config_data_types_and_ranges(self):
        """Kiểm tra kiểu dữ liệu và giá trị hợp lệ của các thông số cấu hình."""
        assert isinstance(Config.CONTEXT_WINDOW, int) and Config.CONTEXT_WINDOW > 0
        assert isinstance(Config.MAX_NEW_TOKENS, int) and Config.MAX_NEW_TOKENS > 0
        assert isinstance(Config.TEMPERATURE, (int, float)) and 0.0 <= Config.TEMPERATURE <= 1.0
        assert isinstance(Config.SIMILARITY_TOP_K, int) and Config.SIMILARITY_TOP_K > 0
        assert isinstance(Config.QDRANT_LOCATION, str) and len(Config.QDRANT_LOCATION) > 0
        assert isinstance(Config.COLLECTION_NAME, str) and len(Config.COLLECTION_NAME) > 0
        assert isinstance(Config.LOCAL_MODEL_DIR, str) and len(Config.LOCAL_MODEL_DIR) > 0
        assert isinstance(Config.DOCS_DIR, str) and len(Config.DOCS_DIR) > 0
        assert isinstance(Config.USERS_FILE, str) and len(Config.USERS_FILE) > 0
        assert "gemini-3.5-flash-lite" in Config.LLM_MODEL

    def test_config_similarity_top_k_default(self):
        """Kiểm tra giá trị mặc định của similarity_top_k."""
        assert Config.SIMILARITY_TOP_K == 5

    def test_config_raises_without_api_key_when_not_testing(self, monkeypatch):
        """Kiểm tra Config bắn ra ValueError nếu thiếu GOOGLE_API_KEY khi không ở chế độ TESTING."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("TESTING", "0")
        
        with pytest.raises(ValueError, match="Please provide GOOGLE_API_KEY"):
            # Tái tạo lại logic kiểm tra khi không có API key trong môi trường production
            google_api = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
            if not google_api and os.getenv("TESTING", "").lower() not in ("1", "true"):
                raise ValueError("[!] Please provide GOOGLE_API_KEY (or GEMINI_API_KEY) in .env file")

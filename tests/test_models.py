from unittest.mock import MagicMock, patch
import os
import pytest
from llama_index.core import Settings
from src.config import Config
import src.models as models

class TestModelsModule:
    @patch("src.models.GoogleGenAIEmbedding")
    @patch("src.models.GoogleGenAI")
    def test_setup_models_with_api_key(self, mock_llm_cls, mock_embed_cls, monkeypatch):
        """Kiểm tra khởi tạo thành công Google Gemini LLM và Google GenAI Embedding khi có API key."""
        from llama_index.core.llms.mock import MockLLM
        from llama_index.core.embeddings import MockEmbedding

        monkeypatch.setattr(Config, "GOOGLE_API_KEY", "test_gemini_key")
        monkeypatch.setattr(Config, "LLM_MODEL", "gemini-3.5-flash-lite")
        monkeypatch.setattr(Config, "EMBEDDING_MODEL", "text-embedding-004")

        mock_llm = MockLLM()
        mock_embed = MockEmbedding(embed_dim=768)
        mock_llm_cls.return_value = mock_llm
        mock_embed_cls.return_value = mock_embed

        models.setup_global_models()

        mock_llm_cls.assert_called_once_with(
            model="gemini-3.5-flash-lite",
            api_key="test_gemini_key",
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_NEW_TOKENS
        )
        assert mock_embed_cls.call_count == 1
        embed_kwargs = mock_embed_cls.call_args.kwargs
        assert embed_kwargs["api_key"] == "test_gemini_key"
        assert embed_kwargs["model_name"] in ("gemini-embedding-001", "text-embedding-004")
        assert embed_kwargs.get("embed_batch_size") == 32
        assert Settings.llm == mock_llm
        assert Settings.embed_model == mock_embed

    def test_setup_models_testing_mode_fallback(self, monkeypatch):
        """Kiểm tra fallback sang MockLLM và MockEmbedding(dim=768) khi ở chế độ TESTING mà không có API key."""
        from llama_index.core.llms.mock import MockLLM
        from llama_index.core.embeddings import MockEmbedding

        monkeypatch.setattr(Config, "GOOGLE_API_KEY", "")
        monkeypatch.setenv("TESTING", "1")

        models.setup_global_models()

        assert isinstance(Settings.llm, MockLLM)
        assert isinstance(Settings.embed_model, MockEmbedding)
        assert Settings.embed_model.embed_dim == 768

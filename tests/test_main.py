from unittest.mock import MagicMock, patch
import pytest
import main
from src.config import Config
from llama_index.core import Settings

class TestMainModule:
    @patch("src.models.HuggingFaceEmbedding")
    @patch("src.models.GoogleGenAI")
    def test_setup_global_models(self, mock_llm_cls, mock_embed_cls, monkeypatch):
        """Kiểm tra hàm khởi tạo model toàn cục setup_global_models() từ src.models."""
        from llama_index.core.llms.mock import MockLLM
        from llama_index.core.embeddings import MockEmbedding
        import src.models as models

        monkeypatch.setattr(Config, "GOOGLE_API_KEY", "test_key")
        mock_llm_instance = MockLLM()
        mock_embed_instance = MockEmbedding(embed_dim=1024)
        mock_llm_cls.return_value = mock_llm_instance
        mock_embed_cls.return_value = mock_embed_instance

        models.setup_global_models()

        mock_llm_cls.assert_called_once()
        mock_embed_cls.assert_called_once()
        assert Settings.llm == mock_llm_instance
        assert Settings.embed_model == mock_embed_instance

    @patch("main.run_backend")
    def test_main_backend_only_flag(self, mock_run_backend):
        """Kiểm tra cờ --backend gọi đúng hàm run_backend."""
        mock_proc = MagicMock()
        mock_run_backend.return_value = mock_proc
        main.main(["--backend", "--backend-port", "8080"])
        mock_run_backend.assert_called_once_with(host="0.0.0.0", port=8080, reload=True)
        mock_proc.wait.assert_called_once()

    @patch("main.run_frontend")
    def test_main_frontend_only_flag(self, mock_run_frontend):
        """Kiểm tra cờ --frontend gọi đúng hàm run_frontend."""
        mock_proc = MagicMock()
        mock_run_frontend.return_value = mock_proc
        main.main(["--frontend", "--frontend-port", "3001"])
        mock_run_frontend.assert_called_once_with(port=3001)
        mock_proc.wait.assert_called_once()

    @patch("main.run_fullstack")
    def test_main_all_fullstack_flag(self, mock_run_fullstack):
        """Kiểm tra cờ --all gọi đúng hàm run_fullstack."""
        main.main(["--all", "--backend-port", "8000", "--frontend-port", "3000"])
        mock_run_fullstack.assert_called_once_with(
            host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            reload=True
        )

    @patch("main.run_fullstack")
    def test_main_default_fullstack(self, mock_run_fullstack):
        """Kiểm tra khi không truyền cờ, mặc định khởi chạy fullstack."""
        main.main([])
        mock_run_fullstack.assert_called_once_with(
            host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            reload=True
        )

    @patch("main.run_fullstack")
    def test_main_no_reload_flag(self, mock_run_fullstack):
        """Kiểm tra cờ --no-reload tắt tính năng reload của Uvicorn."""
        main.main(["--no-reload"])
        mock_run_fullstack.assert_called_once_with(
            host="0.0.0.0",
            backend_port=8000,
            frontend_port=3000,
            reload=False
        )

    def test_terminate_process_handles_none_or_dead(self):
        """Kiểm tra terminate_process không ném exception khi process là None hoặc đã kết thúc."""
        main.terminate_process(None)
        
        dead_proc = MagicMock()
        dead_proc.poll.return_value = 0
        main.terminate_process(dead_proc)
        dead_proc.terminate.assert_not_called()

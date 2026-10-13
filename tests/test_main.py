from unittest.mock import MagicMock, patch
import pytest
import main

class TestMainModule:
    @patch("main.HuggingFaceEmbedding")
    @patch("main.GoogleGenAI")
    def test_setup_global_models(self, mock_llm_cls, mock_embed_cls, monkeypatch):
        """Kiểm tra hàm khởi tạo model toàn cục setup_global_models()."""
        from llama_index.core.llms.mock import MockLLM
        from llama_index.core.embeddings import MockEmbedding

        monkeypatch.setattr(main.Config, "GOOGLE_API_KEY", "test_key")
        mock_llm_instance = MockLLM()
        mock_embed_instance = MockEmbedding(embed_dim=1024)
        mock_llm_cls.return_value = mock_llm_instance
        mock_embed_cls.return_value = mock_embed_instance

        main.setup_global_models()

        mock_llm_cls.assert_called_once()
        mock_embed_cls.assert_called_once()
        assert main.Settings.llm == mock_llm_instance
        assert main.Settings.embed_model == mock_embed_instance

    @patch("main.setup_global_models")
    @patch("main.Qdrant_Manager")
    @patch("main.AuthManager")
    @patch("main.SecureRAGEngine")
    def test_main_cli_successful_login_and_exit(
        self,
        mock_engine_cls,
        mock_auth_cls,
        mock_qm_cls,
        mock_setup_models,
        monkeypatch
    ):
        """Kiểm tra luồng CLI: đăng nhập thành công và gõ exit để thoát."""
        # Giả lập user đăng nhập
        mock_auth_instance = MagicMock()
        mock_auth_instance.login.return_value = {
            "user_id": "U01",
            "name": "Nguyễn Văn A",
            "dept": "HR",
            "role_level": 3
        }
        mock_auth_cls.return_value = mock_auth_instance

        # Chuỗi input từ người dùng: đăng nhập U01, sau đó gõ exit
        user_inputs = iter(["U01", "exit"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(user_inputs))

        main.main()

        mock_setup_models.assert_called_once()
        mock_auth_instance.login.assert_called_once_with("U01")

    @patch("main.setup_global_models")
    @patch("main.Qdrant_Manager")
    @patch("main.AuthManager")
    @patch("main.SecureRAGEngine")
    def test_main_cli_invalid_login(
        self,
        mock_engine_cls,
        mock_auth_cls,
        mock_qm_cls,
        mock_setup_models,
        monkeypatch
    ):
        """Kiểm tra luồng CLI khi người dùng nhập sai User ID."""
        mock_auth_instance = MagicMock()
        mock_auth_instance.login.side_effect = ValueError("[!] User ID not exist!")
        mock_auth_cls.return_value = mock_auth_instance

        user_inputs = iter(["INVALID_USER"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(user_inputs))

        # Chương trình sẽ bắt lỗi và return an toàn
        main.main()

        mock_auth_instance.login.assert_called_once_with("INVALID_USER")
        mock_engine_cls.return_value.chat.assert_not_called()

    @patch("main.setup_global_models")
    @patch("main.Qdrant_Manager")
    @patch("main.AuthManager")
    @patch("main.SecureRAGEngine")
    def test_main_cli_chat_interaction(
        self,
        mock_engine_cls,
        mock_auth_cls,
        mock_qm_cls,
        mock_setup_models,
        monkeypatch
    ):
        """Kiểm tra tương tác hỏi đáp: User nhập câu hỏi, bỏ qua câu rỗng, rồi quit."""
        mock_auth_instance = MagicMock()
        mock_user = {"user_id": "U01", "name": "Nguyễn Văn A", "dept": "HR", "role_level": 3}
        mock_auth_instance.login.return_value = mock_user
        mock_auth_cls.return_value = mock_auth_instance

        mock_engine_instance = MagicMock()
        mock_engine_instance.chat.return_value = "Câu trả lời từ AI"
        mock_engine_cls.return_value = mock_engine_instance

        # Chuỗi input: login -> câu hỏi -> chuỗi rỗng -> quit
        user_inputs = iter(["U01", "Quy trình xin nghỉ phép?", "   ", "quit"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(user_inputs))

        main.main()

        # Engine chỉ được gọi 1 lần với câu hỏi có nội dung, câu rỗng bị bỏ qua
        mock_engine_instance.chat.assert_called_once_with("Quy trình xin nghỉ phép?", mock_user)

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

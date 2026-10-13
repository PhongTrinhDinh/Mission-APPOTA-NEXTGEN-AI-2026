import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app import app
from src.api.dependencies import get_rag_engine, get_auth_manager, get_vector_store
from src.user_manager import AuthManager

class TestFastAPIApp:
    @pytest.fixture
    def client(self, temp_users_file):
        """Khởi tạo TestClient với dependency overrides để test nhanh và độc lập."""
        # Mock AuthManager dùng file test_users.json
        test_auth = AuthManager(users_file=temp_users_file)

        # Mock RAG Engine
        mock_rag = MagicMock()
        test_answer = "Đây là câu trả lời thử nghiệm từ FastAPI RAG."
        mock_rag.chat.return_value = test_answer
        
        mock_resp_obj = MagicMock()
        mock_resp_obj.response = test_answer
        mock_resp_obj.source_nodes = []
        mock_rag.query_with_sources.return_value = mock_resp_obj

        # Mock Vector Store
        mock_vs = MagicMock()
        mock_vs.ingest_data_and_create_index.return_value = MagicMock()

        # Áp dụng dependency overrides
        app.dependency_overrides[get_auth_manager] = lambda: test_auth
        app.dependency_overrides[get_rag_engine] = lambda: mock_rag
        app.dependency_overrides[get_vector_store] = lambda: mock_vs

        # Gán state cho app
        app.state.auth_manager = test_auth
        app.state.rag_engine = mock_rag
        app.state.vector_store = mock_vs
        app.state.is_ready = True

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    def test_root_portal_endpoint(self, client):
        """Kiểm tra trang portal root / trả về HTML 200."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Appota NextGen" in resp.text

    def test_health_check_endpoint(self, client):
        """Kiểm tra endpoint /api/health trả về trạng thái hệ thống."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["is_ready"] is True
        assert "config" in data
        assert "enable_hybrid" in data["config"]
        assert "enable_rerank" in data["config"]

    def test_list_users_endpoint(self, client):
        """Kiểm tra endpoint /api/users trả về danh sách các user."""
        resp = client.get("/api/users")
        assert resp.status_code == 200
        users = resp.json()
        assert len(users) >= 3
        user_ids = [u["user_id"] for u in users]
        assert "U01" in user_ids
        assert "U02" in user_ids
        assert "U99" in user_ids

    def test_login_successful(self, client):
        """Kiểm tra endpoint đăng nhập thành công với User ID hợp lệ."""
        resp = client.post("/api/auth/login", json={"user_id": "U01"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["user"]["user_id"] == "U01"
        assert data["user"]["name"] == "Nguyễn Văn A"
        assert data["user"]["dept"] == "HR"
        assert data["user"]["role_level"] == 3

    def test_login_invalid_user_returns_404(self, client):
        """Kiểm tra đăng nhập với User ID không tồn tại trả về lỗi 404."""
        resp = client.post("/api/auth/login", json={"user_id": "UNKNOWN_USER"})
        assert resp.status_code == 404
        assert "Không tìm thấy tài khoản" in resp.json()["detail"]

    def test_chat_successful_flow(self, client):
        """Kiểm tra gửi câu hỏi chat tra cứu thành công."""
        payload = {
            "user_id": "U01",
            "query": "Quy trình xin nghỉ phép năm 2025 là gì?"
        }
        resp = client.post("/api/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["query"] == payload["query"]
        assert data["response"] == "Đây là câu trả lời thử nghiệm từ FastAPI RAG."
        assert data["user"]["user_id"] == "U01"

    def test_chat_unauthorized_user_returns_401(self, client):
        """Kiểm tra gửi câu hỏi với User ID không hợp lệ trả về lỗi 401."""
        payload = {
            "user_id": "INVALID_ID",
            "query": "Hỏi câu hỏi"
        }
        resp = client.post("/api/chat", json=payload)
        assert resp.status_code == 401
        assert "không hợp lệ" in resp.json()["detail"]

    def test_chat_empty_query_returns_400(self, client):
        """Kiểm tra gửi câu hỏi rỗng trả về lỗi 400."""
        payload = {
            "user_id": "U01",
            "query": "   "
        }
        resp = client.post("/api/chat", json=payload)
        assert resp.status_code == 400
        assert "không được để trống" in resp.json()["detail"]

    def test_ingest_documents_endpoint(self, client):
        """Kiểm tra endpoint /api/ingest kích hoạt lập chỉ mục thành công."""
        resp = client.post("/api/ingest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "thành công" in data["message"]

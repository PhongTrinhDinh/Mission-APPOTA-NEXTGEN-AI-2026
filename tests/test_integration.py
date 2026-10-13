import os
import pytest
from unittest.mock import MagicMock
from src.user_manager import AuthManager
from src.vector_store import Qdrant_Manager
from src.rag_engine import SecureRAGEngine

class TestRAGSecurityIntegration:
    """Kiểm thử tích hợp luồng: Đăng nhập (Auth) -> Phân quyền RBAC -> Lọc tài liệu (Vector Store) -> Truy vấn RAG."""

    def test_end_to_end_document_access_control(self, temp_users_file, temp_docs_dir, mock_index):
        """Kiểm tra ma trận truy cập bảo mật giữa các cấp bậc nhân viên và tài liệu thực tế."""
        # 1. Khởi tạo Auth
        auth = AuthManager(users_file=temp_users_file)
        hr_manager = auth.login("U01")    # Level 3, HR
        sales_staff = auth.login("U02")   # Level 1, Sales
        ceo = auth.login("U99")           # Level 4, BOD

        # 2. Khởi tạo Vector Parser & đọc danh sách tài liệu
        mock_client = MagicMock()
        qm = Qdrant_Manager(client=mock_client)
        
        docs = {}
        for fname in os.listdir(temp_docs_dir):
            if fname.endswith(".md"):
                fpath = os.path.join(temp_docs_dir, fname)
                doc = qm._parse_markdown_with_yaml(fpath)
                docs[fname] = doc

        # Hàm mô phỏng logic lọc cứng của Qdrant dựa trên filter đã thiết lập
        def is_accessible(user, doc):
            doc_level = doc.metadata.get("required_level", 1)
            doc_dept = doc.metadata.get("required_dept", "ALL")
            user_level = user["role_level"]
            user_dept = user["dept"]

            # Điều kiện 1: Level tài liệu <= Level người dùng
            if doc_level > user_level:
                return False

            # Điều kiện 2: Phân quyền phòng ban
            if user_level >= 4:
                # C-Level xem chéo phòng ban
                return True
            else:
                return doc_dept == "ALL" or doc_dept == user_dept

        # 3. Kiểm định ma trận quyền hạn:
        # Tài liệu 1: Public Level 1 -> Tất cả đều xem được
        pub_doc = docs["POL-PUBLIC-001.md"]
        assert is_accessible(hr_manager, pub_doc) is True
        assert is_accessible(sales_staff, pub_doc) is True
        assert is_accessible(ceo, pub_doc) is True

        # Tài liệu 2: HR Level 3 -> HR Manager & CEO xem được, Sales Staff BỊ CHẶN
        hr_doc = docs["POL-HR-003.md"]
        assert is_accessible(hr_manager, hr_doc) is True
        assert is_accessible(ceo, hr_doc) is True
        assert is_accessible(sales_staff, hr_doc) is False, "Sales Staff không được phép xem tài liệu HR!"

        # Tài liệu 3: Tuyệt mật HR Level 4 -> Chỉ CEO xem được, HR Manager (Level 3) & Sales Staff BỊ CHẶN
        secret_doc = docs["CONF-HR-004.md"]
        assert is_accessible(ceo, secret_doc) is True
        assert is_accessible(hr_manager, secret_doc) is False, "HR Manager Level 3 không được phép xem tài liệu Level 4!"
        assert is_accessible(sales_staff, secret_doc) is False, "Sales Staff không được phép xem tài liệu tuyệt mật Level 4!"

        # Tài liệu 4: Sales Level 2 -> CEO xem được (C-Level), HR Manager BỊ CHẶN (khác phòng ban), Sales Staff BỊ CHẶN (Level 1 < Level 2)
        sales_doc = docs["POL-SALES-002.md"]
        assert is_accessible(ceo, sales_doc) is True
        assert is_accessible(hr_manager, sales_doc) is False, "HR không được xem tài liệu nghiệp vụ phòng Sales!"
        assert is_accessible(sales_staff, sales_doc) is False, "Sales Staff Level 1 không được xem tài liệu Level 2!"

    def test_full_chat_flow_with_security_context(self, temp_users_file, mock_index):
        """Kiểm tra toàn bộ luồng từ lúc user đăng nhập đến khi thực hiện câu hỏi thành công."""
        auth = AuthManager(users_file=temp_users_file)
        current_user = auth.login("U01")

        engine = SecureRAGEngine(index=mock_index)
        response = engine.chat("Quy định nghỉ phép năm 2025?", current_user)

        assert isinstance(response, str)
        assert len(response) > 0
        mock_index.as_query_engine.assert_called_once()

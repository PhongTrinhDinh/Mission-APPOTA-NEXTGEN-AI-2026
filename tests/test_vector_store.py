import os
from unittest.mock import MagicMock, patch
import pytest
from src.vector_store import Qdrant_Manager

class TestVectorStoreParsing:
    @pytest.fixture
    def manager(self):
        # Dùng mock client để không cần khởi tạo qdrant DB thật trong unit tests
        mock_client = MagicMock()
        return Qdrant_Manager(client=mock_client, collection_name="test_collection")

    def test_parse_public_document(self, manager, temp_docs_dir):
        """Kiểm tra parse file Public Level 1."""
        file_path = os.path.join(temp_docs_dir, "POL-PUBLIC-001.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["file_id"] == "POL-PUB-001"
        assert doc.metadata["title"] == "Nội quy lao động chung"
        assert doc.metadata["required_level"] == 1
        assert doc.metadata["required_dept"] == "ALL"
        assert "Mọi nhân viên cần tuân thủ" in doc.text

    def test_parse_hr_level3_document(self, manager, temp_docs_dir):
        """Kiểm tra parse file HR có clearance_level: LEVEL_3."""
        file_path = os.path.join(temp_docs_dir, "POL-HR-003.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["file_id"] == "POL-HR-003"
        assert doc.metadata["required_level"] == 3
        assert doc.metadata["required_dept"] == "HR"
        assert "Quy chế khen thưởng" in doc.text

    def test_parse_hr_level4_strict_document(self, manager, temp_docs_dir):
        """Kiểm tra parse file Tuyệt mật cấp 4 LEVEL_4_STRICT."""
        file_path = os.path.join(temp_docs_dir, "CONF-HR-004.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["file_id"] == "CONF-HR-004"
        assert doc.metadata["required_level"] == 4
        assert doc.metadata["required_dept"] == "HR"

    def test_parse_sales_level2_document(self, manager, temp_docs_dir):
        """Kiểm tra parse file Sales Level 2."""
        file_path = os.path.join(temp_docs_dir, "POL-SALES-002.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["file_id"] == "POL-SALES-002"
        assert doc.metadata["required_level"] == 2
        assert doc.metadata["required_dept"] == "Sales"

    def test_parse_document_without_yaml(self, manager, temp_docs_dir):
        """Kiểm tra fallback an toàn khi file markdown không có frontmatter YAML."""
        file_path = os.path.join(temp_docs_dir, "README_NO_YAML.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["required_level"] == 1
        assert doc.metadata["required_dept"] == "ALL"
        assert "Hướng dẫn sử dụng hệ thống" in doc.text

    def test_parse_document_with_malformed_yaml(self, manager, temp_docs_dir):
        """Kiểm tra xử lý ngoại lệ khi YAML bị cú pháp lỗi mà không làm sập ứng dụng."""
        file_path = os.path.join(temp_docs_dir, "MALFORMED.md")
        doc = manager._parse_markdown_with_yaml(file_path)

        assert doc.metadata["required_level"] == 1
        assert doc.metadata["required_dept"] == "ALL"

    def test_parse_real_documents_in_data_dir(self, manager):
        """Kiểm tra thử nghiệm thực tế trên tập file data gốc của dự án."""
        real_data_dir = "data"
        if not os.path.exists(real_data_dir):
            pytest.skip("Thư mục data thực tế không tồn tại")

        sample_conf = os.path.join(real_data_dir, "CONF-HR-SEC-001_Quy_trinh_ky_luat_sa_thai_va_bang_luong_nhay_cam.md")
        if os.path.exists(sample_conf):
            doc = manager._parse_markdown_with_yaml(sample_conf)
            assert doc.metadata["file_id"] == "CONF-HR-SEC-001"
            assert doc.metadata["required_level"] == 4
            assert doc.metadata["required_dept"] == "HR"

class TestVectorStoreIngestion:
    @patch("src.vector_store.VectorStoreIndex.from_documents")
    def test_ingest_data_and_create_index(self, mock_from_documents, temp_docs_dir):
        """Kiểm tra quy trình quét thư mục, lọc chỉ lấy file .md và gọi from_documents."""
        mock_client = MagicMock()
        manager = Qdrant_Manager(client=mock_client, collection_name="test_collection")
        mock_from_documents.return_value = MagicMock()

        index = manager.ingest_data_and_create_index(docs_dir=temp_docs_dir, show_progress=False)

        assert index is not None
        mock_from_documents.assert_called_once()
        
        # Kiểm tra danh sách documents truyền vào from_documents
        call_args = mock_from_documents.call_args
        documents = call_args[0][0]
        # temp_docs_dir có 6 file .md và 1 file .txt -> chỉ nhận đúng 6 file .md
        assert len(documents) == 6
        for doc in documents:
            assert hasattr(doc, "metadata")
            assert "required_level" in doc.metadata
            assert "required_dept" in doc.metadata

        # Kiểm tra storage_context được truyền đúng vào from_documents
        kwargs = call_args[1]
        assert "storage_context" in kwargs

    def test_recreate_hybrid_collection(self):
        """Kiểm tra recreate_hybrid_collection xóa collection cũ và khởi tạo Hybrid Store."""
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        manager = Qdrant_Manager(client=mock_client, collection_name="test_collection")
        manager.recreate_hybrid_collection("test_collection")
        mock_client.delete_collection.assert_called_once_with("test_collection")
        assert manager.vector_store.enable_hybrid is True

    def test_hybrid_search_initialization(self):
        """Kiểm tra khởi tạo Qdrant Vector Store với cấu hình Hybrid Search BM25."""
        mock_client = MagicMock()
        manager = Qdrant_Manager(client=mock_client, enable_hybrid=True, fastembed_sparse_model="Qdrant/bm25")
        assert manager.vector_store.enable_hybrid is True
        assert manager.vector_store.fastembed_sparse_model == "Qdrant/bm25"

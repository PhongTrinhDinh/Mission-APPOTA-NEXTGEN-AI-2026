import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock

# Đặt biến môi trường TESTING để Config không yêu cầu bắt buộc có HF API key ngoài đời thực
os.environ["TESTING"] = "1"

@pytest.fixture
def sample_users_data():
    return [
        {
            "user_id": "U01",
            "name": "Nguyễn Văn A",
            "company": "Appota",
            "dept": "HR",
            "role_level": 3
        },
        {
            "user_id": "U02",
            "name": "Trần Thị B",
            "company": "Kdata",
            "dept": "Sales",
            "role_level": 1
        },
        {
            "user_id": "U03",
            "name": "Lê Văn C",
            "company": "Appota",
            "dept": "Engineering",
            "role_level": 1
        },
        {
            "user_id": "U99",
            "name": "Tổng Giám Đốc",
            "company": "Appota Group",
            "dept": "BOD",
            "role_level": 4
        },
        {
            "user_id": "U100",
            "name": "Chủ Tịch HĐQT",
            "company": "Appota Group",
            "dept": "BOD",
            "role_level": 5
        }
    ]

@pytest.fixture
def temp_users_file(sample_users_data, tmp_path):
    file_path = tmp_path / "test_users.json"
    file_path.write_text(json.dumps(sample_users_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(file_path)

@pytest.fixture
def temp_docs_dir(tmp_path):
    docs_dir = tmp_path / "test_docs"
    docs_dir.mkdir()

    # 1. Tài liệu Public Level 1
    (docs_dir / "POL-PUBLIC-001.md").write_text("""---
id: "POL-PUB-001"
title: "Nội quy lao động chung"
access_control:
  classification: "PUBLIC"
  clearance_level: "LEVEL_1"
---
# Nội quy lao động chung
Mọi nhân viên cần tuân thủ quy định thời gian làm việc từ 8h30 đến 17h30.
""", encoding="utf-8")

    # 2. Tài liệu HR Level 3
    (docs_dir / "POL-HR-003.md").write_text("""---
id: "POL-HR-003"
title: "Quy chế khen thưởng và tăng lương nội bộ"
access_control:
  classification: "RESTRICTED_HR_ONLY"
  clearance_level: "LEVEL_3"
---
# Quy chế khen thưởng
Chính sách tăng lương dành cho quản lý phòng ban xem xét.
""", encoding="utf-8")

    # 3. Tài liệu Tuyệt mật Level 4 (HR / C-Level)
    (docs_dir / "CONF-HR-004.md").write_text("""---
id: "CONF-HR-004"
title: "Khung thang bảng lương C-Level và sa thải đặc biệt"
access_control:
  classification: "RESTRICTED_HR_ONLY"
  clearance_level: "LEVEL_4_STRICT"
---
# Tài liệu tuyệt mật C-Level
Chỉ Ban giám đốc và CHRO được quyền truy cập.
""", encoding="utf-8")

    # 4. Tài liệu Sales Level 2
    (docs_dir / "POL-SALES-002.md").write_text("""---
id: "POL-SALES-002"
title: "Quy chế hoa hồng phòng Kinh doanh"
access_control:
  classification: "SALES_ONLY"
  clearance_level: "LEVEL_2"
---
# Hoa hồng kinh doanh
Chiết khấu hoa hồng cho Sales Lead và Chuyên viên kinh doanh.
""", encoding="utf-8")

    # 5. File thuần Markdown không có YAML frontmatter
    (docs_dir / "README_NO_YAML.md").write_text("""# Hướng dẫn sử dụng hệ thống
Tài liệu hướng dẫn chung không khai báo frontmatter.
""", encoding="utf-8")

    # 6. File với YAML bị lỗi cú pháp
    (docs_dir / "MALFORMED.md").write_text("""---
id: [malformed yaml: {unclosed:
---
# Tài liệu lỗi YAML
Nội dung tài liệu với YAML không hợp lệ.
""", encoding="utf-8")

    # 7. File không phải markdown (để kiểm tra xem có bị quét nhầm không)
    (docs_dir / "note.txt").write_text("Đây là file text bình thường, không phải .md", encoding="utf-8")

    return str(docs_dir)

@pytest.fixture
def mock_source_node():
    node = MagicMock()
    node.metadata = {"title": "Tài liệu mẫu", "required_level": 1, "required_dept": "ALL"}
    return node

@pytest.fixture
def mock_query_engine(mock_source_node):
    engine = MagicMock()
    mock_resp = MagicMock()
    mock_resp.response = "Đây là câu trả lời thử nghiệm từ AI."
    mock_resp.source_nodes = [mock_source_node]
    engine.query.return_value = mock_resp
    return engine

@pytest.fixture
def mock_index(mock_query_engine):
    index = MagicMock()
    index.as_query_engine.return_value = mock_query_engine
    return index

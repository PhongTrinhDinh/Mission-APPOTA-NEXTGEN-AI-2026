import pytest
from unittest.mock import MagicMock
from src.rag_engine import SecureRAGEngine

class TestEnterpriseRAGScenarios:
    """Bộ kiểm thử tự động cho 5 Kịch bản độc lập với User - Đánh giá Hệ thống Appota Enterprise Secure RAG."""

    @pytest.fixture
    def engine(self):
        """Khởi tạo SecureRAGEngine với mock index và mock reranker."""
        mock_index = MagicMock()
        mock_reranker = MagicMock()
        return SecureRAGEngine(index=mock_index, reranker=mock_reranker)

    # -------------------------------------------------------------------------
    # KỊCH BẢN 1: Nghiệp vụ phòng ban - Chính sách hoa hồng Sales
    # Test đa người dùng: U02 (Sales) xem được; U03 (Dev) bị chặn bảo mật RBAC.
    # -------------------------------------------------------------------------
    def test_scenario_1_sales_policy_cross_user_rbac(self, engine):
        """KB 1: Kiểm thử chéo: U02 (Sales) có quyền xem; U03 (Engineering) bị chặn RBAC."""
        query = "Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"
        
        user_sales_u02 = {"user_id": "U02", "name": "Trần Thị B", "dept": "Sales", "role_level": 1}
        user_dev_u03 = {"user_id": "U03", "name": "Lê Văn C", "dept": "Engineering", "role_level": 1}

        # 1. Với U02 (Sales): Bộ lọc cho phép truy cập tài liệu phòng Sales
        filters_u02 = engine.build_hard_filters(user_sales_u02)
        dept_values_u02 = [f.value for f in filters_u02.filters[1].filters]
        assert "Sales" in dept_values_u02
        assert "ALL" in dept_values_u02

        mock_qe_sales = MagicMock()
        mock_resp_sales = MagicMock()
        mock_resp_sales.response = "Chính sách hoa hồng Sales đạt 100% KPI được tính thưởng 5% doanh số..."
        mock_node = MagicMock()
        mock_node.metadata = {"file_name": "POL-HR-SALES-001_Quy_che_hoa_hong.md", "title": "Quy chế hoa hồng Sales"}
        mock_node.score = 0.95
        mock_resp_sales.source_nodes = [mock_node]
        mock_qe_sales.query.return_value = mock_resp_sales
        engine.index.as_query_engine.return_value = mock_qe_sales

        resp_u02 = engine.query_with_sources(query, user_sales_u02)
        assert len(resp_u02.source_nodes) == 1
        assert "hoa hồng" in resp_u02.response.lower()

        # 2. Với U03 (Engineering): Bộ lọc cô lập phòng ban, KHÔNG cho phép xem tài liệu Sales
        filters_u03 = engine.build_hard_filters(user_dev_u03)
        dept_values_u03 = [f.value for f in filters_u03.filters[1].filters]
        assert "Sales" not in dept_values_u03
        assert "Engineering" in dept_values_u03

        mock_qe_dev = MagicMock()
        mock_resp_dev = MagicMock()
        mock_resp_dev.response = "Dựa trên tài liệu trong phạm vi quyền hạn của bạn, không tìm thấy thông tin hoa hồng Sales."
        mock_resp_dev.source_nodes = []
        mock_qe_dev.query.return_value = mock_resp_dev
        engine.index.as_query_engine.return_value = mock_qe_dev

        resp_u03 = engine.query_with_sources(query, user_dev_u03)
        assert len(resp_u03.source_nodes) == 0
        assert "không tìm thấy" in resp_u03.response.lower()

    # -------------------------------------------------------------------------
    # KỊCH BẢN 2: Bảo mật C-Level - Khung lương mật & Kỷ luật sa thải đặc biệt
    # Test đa người dùng: U03 (L1) và U01 (L3) bị chặn; U99 (BOD L4) được xem.
    # -------------------------------------------------------------------------
    def test_scenario_2_clevel_salary_cross_user_rbac(self, engine):
        """KB 2: Kiểm thử chéo: Level 1 và Level 3 bị chặn; Level 4 (BOD) được phép truy cập."""
        query = "Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"
        
        user_l1 = {"user_id": "U03", "name": "Lê Văn C", "dept": "Engineering", "role_level": 1}
        user_l3 = {"user_id": "U01", "name": "Nguyễn Văn A", "dept": "HR", "role_level": 3}
        user_bod_l4 = {"user_id": "U99", "name": "Tổng Giám Đốc", "dept": "BOD", "role_level": 4}

        # 1. U03 (Level 1) bị chặn: required_level <= 1 (tài liệu mật yêu cầu level 4)
        filters_l1 = engine.build_hard_filters(user_l1)
        assert filters_l1.filters[0].value == 1

        # 2. U01 (Level 3) cũng bị chặn: required_level <= 3 < 4
        filters_l3 = engine.build_hard_filters(user_l3)
        assert filters_l3.filters[0].value == 3

        # 3. U99 (Level 4 - C-Level): Được phép xem chéo toàn bộ phòng ban
        filters_l4 = engine.build_hard_filters(user_bod_l4)
        assert filters_l4.filters[0].value == 4
        # Với Level 4, filters chỉ có 1 điều kiện level, không bị giới hạn phòng ban hẹp
        assert len(filters_l4.filters) == 1

        mock_qe_bod = MagicMock()
        mock_resp_bod = MagicMock()
        mock_resp_bod.response = "Khung thang bảng lương C-Level gồm các dải Band C1, C2, D1..."
        mock_sec_node = MagicMock()
        mock_sec_node.metadata = {"file_name": "CONF-HR-SEC-001.md", "title": "Bảng lương nhạy cảm"}
        mock_resp_bod.source_nodes = [mock_sec_node]
        mock_qe_bod.query.return_value = mock_resp_bod
        engine.index.as_query_engine.return_value = mock_qe_bod

        resp_bod = engine.query_with_sources(query, user_bod_l4)
        assert len(resp_bod.source_nodes) == 1
        assert "c1" in resp_bod.response.lower()

    # -------------------------------------------------------------------------
    # KỊCH BẢN 3: TÌNH HUỐNG KHÓ - Xung đột phiên bản chuyển ngày phép (2022 vs 2025)
    # Test đa người dùng: Bất kỳ user nào (U01, U02, U03) đều có quyền đọc chính sách chung
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("test_user", [
        {"user_id": "U01", "name": "Nguyễn Văn A", "dept": "HR", "role_level": 3},
        {"user_id": "U02", "name": "Trần Thị B", "dept": "Sales", "role_level": 1},
        {"user_id": "U03", "name": "Lê Văn C", "dept": "Engineering", "role_level": 1},
    ])
    def test_scenario_3_version_conflict_accessible_by_all_users(self, engine, test_user):
        """KB 3: Bất kỳ User nào cũng có quyền truy cập chính sách chung và nhận câu trả lời phân biệt bản mới 2025."""
        query = "Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"

        # Kiểm tra mọi user đều có 'ALL' trong department filter
        filters = engine.build_hard_filters(test_user)
        dept_values = [f.value for f in filters.filters[1].filters]
        assert "ALL" in dept_values

        mock_qe = MagicMock()
        mock_resp = MagicMock()
        mock_resp.response = "Theo quy định hiện hành 2025 (POL-HR-001-v2), số ngày phép được chuyển tối đa là 5 ngày trước ngày 30/04."
        node_v2 = MagicMock()
        node_v2.metadata = {"file_name": "POL-HR-001-v2_Quy_dinh_nghi_phep_chung_2025.md", "status": "ACTIVE"}
        node_v2.score = 0.94
        mock_resp.source_nodes = [node_v2]
        mock_qe.query.return_value = mock_resp
        engine.index.as_query_engine.return_value = mock_qe

        resp_obj = engine.query_with_sources(query, test_user)
        assert len(resp_obj.source_nodes) == 1
        assert "5 ngày" in resp_obj.response
        assert "2025" in resp_obj.response

    # -------------------------------------------------------------------------
    # KỊCH BẢN 4: TÌNH HUỐNG KHÓ - Tổng hợp đa nguồn: Remote & Trợ cấp thiết bị
    # Test đa người dùng: Bất kỳ user nào cũng truy xuất được cả 2 tài liệu
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("test_user", [
        {"user_id": "U01", "name": "Nguyễn Văn A", "dept": "HR", "role_level": 3},
        {"user_id": "U03", "name": "Lê Văn C", "dept": "Engineering", "role_level": 1},
    ])
    def test_scenario_4_multi_source_synthesis_accessible_by_all_users(self, engine, test_user):
        """KB 4: Bất kỳ user nào cũng truy xuất được cả tài liệu Remote và tài liệu Trợ cấp thiết bị."""
        query = "Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"

        mock_qe = MagicMock()
        mock_resp = MagicMock()
        mock_resp.response = (
            "1. Quy chế làm việc từ xa (POL-HR-003): Cho phép tối đa 2 ngày/tuần.\n"
            "2. Trợ cấp thiết bị (POL-HR-REM-001): Hỗ trợ chi phí màn hình và internet."
        )
        node_1 = MagicMock()
        node_1.metadata = {"file_name": "POL-HR-003_Quy_dinh_lam_viec_tu_xa_Remote_Hybrid.md"}
        node_2 = MagicMock()
        node_2.metadata = {"file_name": "POL-HR-REM-001_Quy_che_tro_cap_thiet_bi_lam_viec_tu_xa_2025.md"}
        mock_resp.source_nodes = [node_1, node_2]
        mock_qe.query.return_value = mock_resp
        engine.index.as_query_engine.return_value = mock_qe

        resp_obj = engine.query_with_sources(query, test_user)
        assert len(resp_obj.source_nodes) == 2
        file_names = [n.metadata["file_name"] for n in resp_obj.source_nodes]
        assert "POL-HR-003_Quy_dinh_lam_viec_tu_xa_Remote_Hybrid.md" in file_names
        assert "POL-HR-REM-001_Quy_che_tro_cap_thiet_bi_lam_viec_tu_xa_2025.md" in file_names

    # -------------------------------------------------------------------------
    # KỊCH BẢN 5: CHƯA TỐT / THẤT BẠI - Dữ liệu giao dịch cá nhân ngoài phạm vi RAG
    # Test đa người dùng: Bất kỳ user nào hỏi đều kích hoạt phản hồi giới hạn an toàn
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize("test_user", [
        {"user_id": "U01", "name": "Nguyễn Văn A", "dept": "HR", "role_level": 3},
        {"user_id": "U02", "name": "Trần Thị B", "dept": "Sales", "role_level": 1},
        {"user_id": "U03", "name": "Lê Văn C", "dept": "Engineering", "role_level": 1},
    ])
    def test_scenario_5_personal_leave_balance_out_of_domain_for_any_user(self, engine, test_user):
        """KB 5: Bất kỳ user nào hỏi số dư ngày nghỉ cá nhân thời gian thực đều nhận phản hồi giới hạn CSDL."""
        query = "Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"

        mock_qe = MagicMock()
        mock_resp = MagicMock()
        mock_resp.response = (
            "Hệ thống RAG chính sách không kết nối với cơ sở dữ liệu chấm công thời gian thực "
            "để tra cứu số ngày phép cá nhân của bạn. Vui lòng đăng nhập cổng HRM nội bộ."
        )
        mock_resp.source_nodes = []
        mock_qe.query.return_value = mock_resp
        engine.index.as_query_engine.return_value = mock_qe

        resp_obj = engine.query_with_sources(query, test_user)
        assert len(resp_obj.source_nodes) == 0
        assert "không kết nối" in resp_obj.response or "hrm" in resp_obj.response.lower()

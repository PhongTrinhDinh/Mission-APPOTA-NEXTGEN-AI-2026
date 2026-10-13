import json
import pytest
from src.user_manager import AuthManager

class TestAuthManager:
    def test_load_default_users_file(self):
        """Kiểm tra việc nạp dữ liệu từ file users.json mặc định của hệ thống."""
        auth = AuthManager()
        assert len(auth.users) >= 3
        assert "U01" in auth.users
        assert "U02" in auth.users
        assert "U03" in auth.users

    def test_user_data_structure(self):
        """Kiểm tra định dạng và cấu trúc dữ liệu người dùng."""
        auth = AuthManager()
        for user_id, user_data in auth.users.items():
            assert "user_id" in user_data
            assert "name" in user_data
            assert "company" in user_data
            assert "dept" in user_data
            assert "role_level" in user_data
            assert isinstance(user_data["role_level"], int)
            assert user_data["user_id"] == user_id

    def test_login_successful_existing_users(self):
        """Kiểm tra luồng đăng nhập thành công với các user hợp lệ."""
        auth = AuthManager()
        
        # Test U01: HR Manager Level 3
        u1 = auth.login("U01")
        assert u1["name"] == "Nguyễn Văn A"
        assert u1["dept"] == "HR"
        assert u1["role_level"] == 3

        # Test U02: Sales Staff Level 1
        u2 = auth.login("U02")
        assert u2["name"] == "Trần Thị B"
        assert u2["dept"] == "Sales"
        assert u2["role_level"] == 1

        # Test U03: Engineering Staff Level 1
        u3 = auth.login("U03")
        assert u3["name"] == "Lê Văn C"
        assert u3["dept"] == "Engineering"
        assert u3["role_level"] == 1

    def test_login_invalid_user_raises_value_error(self):
        """Kiểm tra bắn lỗi khi user_id không tồn tại."""
        auth = AuthManager()
        with pytest.raises(ValueError, match=r"\[!\] User ID not exist!"):
            auth.login("NON_EXISTENT_ID")

    def test_login_empty_user_id_raises_value_error(self):
        """Kiểm tra bắn lỗi khi user_id rỗng."""
        auth = AuthManager()
        with pytest.raises(ValueError, match=r"\[!\] User ID not exist!"):
            auth.login("")

    def test_custom_users_file(self, temp_users_file):
        """Kiểm tra khởi tạo AuthManager với file dữ liệu tùy chọn từ fixture."""
        auth = AuthManager(users_file=temp_users_file)
        
        # Kiểm tra user cấp C-Level từ fixture
        ceo = auth.login("U99")
        assert ceo["name"] == "Tổng Giám Đốc"
        assert ceo["dept"] == "BOD"
        assert ceo["role_level"] == 4

        chair = auth.login("U100")
        assert chair["name"] == "Chủ Tịch HĐQT"
        assert chair["role_level"] == 5

    def test_empty_users_file(self, tmp_path):
        """Kiểm tra khởi tạo với file json rỗng []."""
        empty_file = tmp_path / "empty_users.json"
        empty_file.write_text("[]", encoding="utf-8")
        
        auth = AuthManager(users_file=str(empty_file))
        assert len(auth.users) == 0
        with pytest.raises(ValueError):
            auth.login("U01")

    def test_file_not_found(self):
        """Kiểm tra xử lý lỗi khi file người dùng không tồn tại."""
        with pytest.raises(FileNotFoundError):
            AuthManager(users_file="non_existent_file.json")

    def test_malformed_json_file(self, tmp_path):
        """Kiểm tra xử lý lỗi khi file JSON người dùng bị hỏng."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json", encoding="utf-8")
        
        with pytest.raises(json.JSONDecodeError):
            AuthManager(users_file=str(bad_file))

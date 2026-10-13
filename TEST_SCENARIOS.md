# BÁO CÁO ĐÁNH GIÁ & 5 KỊCH BẢN KIỂM THỬ HỆ THỐNG APPOTA ENTERPRISE SECURE RAG
*(Phiên bản Chuẩn hóa: Độc lập với User & Kiểm thử Phân quyền Đa chiều RBAC)*

> **Dự án:** Appota NextGen Enterprise Secure RAG System  
> **Kiến trúc:** FastAPI Backend + Next.js 16 Client + Qdrant Hybrid Search (Dense E5-large GPU + Sparse BM25) + FlashRank Reranker + Google Gemini (`gemini-3.5-flash-lite`) + RBAC Hard Filtering.  
> **Ngày cập nhật:** 13/10/2026  

---

## 1. TỔNG QUAN VỀ THIẾT KẾ 5 KỊCH BẢN ĐỘC LẬP VỚI USER

Trong môi trường doanh nghiệp thực tế, **kịch bản kiểm thử không được gắn chết vào một cá nhân cụ thể**. Thay vào đó, kịch bản phải mang tính chuẩn hóa nghiệp vụ để **bất kỳ tài khoản nào cũng có thể thực thi**, qua đó kiểm chứng được tính đúng đắn của **Cơ chế Phân quyền & Cách ly Dữ liệu (RBAC Security Isolation)**:
- **Cùng 1 câu hỏi:** User có quyền hạn hợp lệ sẽ nhận được câu trả lời chi tiết và tài liệu trích dẫn.
- **Cùng 1 câu hỏi:** User không có quyền hạn (khác phòng ban hoặc cấp bậc thấp hơn) sẽ bị chặn ngay tại tầng Vector Database trước khi dữ liệu được nạp vào LLM (Zero Data Leakage).

---

## 2. MA TRẬN PHÂN QUYỀN CHÉO (CROSS-USER TESTING MATRIX)

Bảng ma trận thể hiện phản ứng của hệ thống khi 4 nhóm người dùng đại diện gửi câu hỏi của 5 kịch bản:

| Mã KB | Tên Kịch Bản | Câu Hỏi Chuẩn Hóa | `U02` - Sales (L1) | `U03` - Dev (L1) | `U01` - HR Manager (L3) | `U99` - BOD / C-Level (L4/5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KB-01** | **Chính sách hoa hồng Sales** *(Nghiệp vụ phòng ban)* | *"Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"* | ✅ **XEM ĐƯỢC**<br>(Đúng phòng Sales) | 🔒 **BỊ CHẶN RBAC**<br>(Khác phòng ban) | 🔒 **BỊ CHẶN RBAC**<br>(Khác phòng ban) | ✅ **XEM ĐƯỢC**<br>(C-Level xem toàn bộ) |
| **KB-02** | **Bảng lương mật C-Level** *(Bảo mật cấp bậc)* | *"Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"* | 🔒 **BỊ CHẶN RBAC**<br>(Level 1 < Level 4) | 🔒 **BỊ CHẶN RBAC**<br>(Level 1 < Level 4) | 🔒 **BỊ CHẶN RBAC**<br>(Level 3 < Level 4) | ✅ **XEM ĐƯỢC**<br>(Level ≥ 4 hợp lệ) |
| **KB-03** | **Xung đột chuyển phép** *(Tình huống khó: Đa bản)* | *"Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"* | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) |
| **KB-04** | **Remote & Thiết bị** *(Tình huống khó: Đa nguồn)* | *"Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"* | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) | ✅ **XEM ĐƯỢC**<br>(Chính sách chung) |
| **KB-05** | **Số dư phép cá nhân** *(Chưa tốt / Thất bại)* | *"Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"* | ⚠️ **TỪ CHỐI AN TOÀN**<br>(Thiếu CSDL chấm công) | ⚠️ **TỪ CHỐI AN TOÀN**<br>(Thiếu CSDL chấm công) | ⚠️ **TỪ CHỐI AN TOÀN**<br>(Thiếu CSDL chấm công) | ⚠️ **TỪ CHỐI AN TOÀN**<br>(Thiếu CSDL chấm công) |

---

## 3. PHÂN TÍCH CHUYÊN SÂU TỪNG KỊCH BẢN

### 🟢 KỊCH BẢN 1: Phân Quyền Phòng Ban - Chính Sách Hoa Hồng & Doanh Số Sales
- **Bản chất:** Kiểm tra năng lực cô lập phòng ban (Department Isolation).
- **Câu hỏi:**  
  > *"Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"*
- **Tài liệu nguồn:** `POL-HR-SALES-001_Quy_che_hoa_hong_va_thuong_doanh_so_Khoi_Kinh_doanh.md` (`required_dept: "Sales"`, `required_level: 1`).
- **Cơ chế hoạt động:**
  - **Với `U02` (Sales L1):** Bộ lọc Qdrant thỏa mãn (`department in ['Sales', 'ALL']`). Hybrid Search tìm thấy các đoạn trích tỷ lệ hoa hồng; FlashRank chấm điểm > 0.92; Gemini trả lời chi tiết về các mốc KPI và điều kiện nghiệm thu hợp đồng.
  - **Với `U03` (Dev L1) hoặc `U01` (HR L3):** Bộ lọc Qdrant chỉ cho phép (`department in ['Engineering', 'ALL']` hoặc `['HR', 'ALL']`). Toàn bộ chunk của `POL-HR-SALES-001` bị lọc bỏ hoàn toàn. Gemini phản hồi an toàn: không tìm thấy thông tin trong phạm vi quyền hạn.
- **Ý nghĩa:** Chứng minh hệ thống không bị rò rỉ dữ liệu chéo giữa các phòng ban.

---

### 🟢 KỊCH BẢN 2: Bảo Mật Cấp Bậc - Bảng Lương Mật C-Level & Sa Thải Đặc Biệt
- **Bản chất:** Kiểm tra năng lực bảo vệ tài liệu cấp bậc tối mật (Clearance Level Isolation).
- **Câu hỏi:**  
  > *"Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"*
- **Tài liệu mục tiêu:** `CONF-HR-SEC-001_Quy_trinh_ky_luat_sa_thai_va_bang_luong_nhay_cam.md` (`required_level: 4`, `required_dept: "HR"`).
- **Cơ chế hoạt động:**
  - **Với `U03` (Level 1) và `U01` (Level 3):** Qdrant Hard Filter áp đặt điều kiện `required_level <= user_level`. Vì tài liệu yêu cầu Level 4, điều kiện này bị vi phạm ngay lập tức. Không một vector nào được đưa vào bộ nhớ đệm hay context của LLM (Zero Data Leakage).
  - **Với `U99` (Level 4/5 - BOD):** Bộ lọc `user_level >= 4` kích hoạt đặc quyền C-Level (không bị giới hạn phòng ban hẹp). Dữ liệu được giải mã và Gemini trả lời khung lương dải Band C1, C2, D1 kèm quy trình thu hồi quyền trong 15 phút.
- **Ý nghĩa:** Đảm bảo bí mật kinh doanh và an toàn thông tin nhân sự cấp cao.

---

### 🟡 KỊCH BẢN 3: Tình Huống Khó - Xung Đột Thời Gian & Đa Phiên Bản (2022 vs 2025)
- **Bản chất:** Kiểm tra khả năng xử lý dữ liệu lỗi thời (Data Staleness / Temporal Conflict).
- **Câu hỏi:**  
  > *"Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"*
- **Tài liệu liên quan:**
  - `POL-HR-001-v1` (2022, `status: EXPIRED`): Chuyển tối đa 3 ngày trước 31/03.
  - `POL-HR-001-v2` (2025, `status: ACTIVE`): Chuyển tối đa 5 ngày trước 30/04.
  - Cả 2 tài liệu đều có `required_dept: "ALL"`, `required_level: 1` -> **Mọi user đều truy cập được**.
- **Cơ chế hoạt động:**
  - Sparse BM25 nhận diện các token `"hiện hành"`, `"2025"`.
  - FlashRank Reranker đọc metadata `status: "ACTIVE"` và đẩy điểm số của bản 2025 lên đầu danh sách ứng viên.
  - Gemini LLM giải thích chuẩn xác: Quy định hiện hành năm 2025 cho phép chuyển **5 ngày trước ngày 30/04**, phân biệt rõ với quy định cũ 2022.
- **Ý nghĩa:** Giải quyết bài toán phổ biến nhất trong RAG doanh nghiệp: văn bản mới thay thế văn bản cũ.

---

### 🟡 KỊCH BẢN 4: Tình Huống Khó - Tổng Hợp Đa Nguồn Độc Lập (Remote & Trợ Cấp)
- **Bản chất:** Kiểm tra khả năng tổng hợp đa tài liệu (Multi-hop Synthesis).
- **Câu hỏi:**  
  > *"Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"*
- **Tài liệu liên quan:**
  - `POL-HR-003_Quy_dinh_lam_viec_tu_xa_Remote_Hybrid.md` (Quy định đăng ký ngày công remote tối đa 2 ngày/tuần).
  - `POL-HR-REM-001_Quy_che_tro_cap_thiet_bi_lam_viec_tu_xa_2025.md` (Định mức tiền mua màn hình, đường truyền mạng).
- **Cơ chế hoạt động:**
  - Cấu hình `RETRIEVAL_TOP_K = 15` kéo đủ chunks của cả 2 tài liệu.
  - FlashRank Reranker chọn lọc và dung hòa các đoạn trích bổ trợ cho cả 2 vế câu hỏi.
  - Gemini LLM tổng hợp cấu trúc câu trả lời mạch lạc gồm: Phần 1 (Quy chế làm từ xa) và Phần 2 (Chế độ trợ cấp trang thiết bị).
- **Ý nghĩa:** Phục vụ các câu hỏi tổng hợp chính sách đa chiều của người lao động.

---

### 🔴 KỊCH BẢN 5: Chưa Tốt / Thất Bại - Dữ Liệu Giao Dịch Cá Nhân Thời Gian Thực
- **Bản chất:** Xác định giới hạn kỹ thuật (Boundary Limitation) của Document Policy RAG.
- **Câu hỏi:**  
  > *"Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"*
- **Nguyên nhân thất bại bản chất:**
  - Hệ thống hiện tại chỉ chứa kho **tài liệu quy chế tĩnh dạng Markdown**.
  - Hệ thống **chưa kết nối API với CSDL chấm công / ERP / HRIS giao dịch thời gian thực**.
- **Hành vi thực tế:**
  - Không có vector nào chứa lịch sử chấm công cá nhân của người đang hỏi.
  - Gemini LLM phản hồi: Hệ thống không lưu trữ dữ liệu số dư ngày phép cá nhân thời gian thực và chỉ có thể trích dẫn công thức tính chung; hướng dẫn người dùng kiểm tra cổng HRM nội bộ.
  - Sản phẩm thất bại trong việc trả về con số định lượng cá nhân cụ thể.
- **Đề xuất nâng cấp (Future Roadmap):**
  - Bổ sung **Multi-Agent Tool Calling / Text-to-SQL**: Khi phát hiện ý định hỏi dữ liệu giao dịch cá nhân (`intent: personal_leave_balance`), Agent sẽ gọi Tool truy vấn SQL Database thay vì Vector Store.

---

## 4. HƯỚNG DẪN THỰC NGHIỆM TRỰC TIẾP TRÊN GIAO DIỆN

1. Khởi động hệ thống: `python -m main`.
2. Mở trình duyệt tại: `http://localhost:3000`.
3. **Thử nghiệm Kịch bản 1 (Hoa hồng Sales):**
   - Chọn nhân viên `U02 (Sales)` -> Click **KB 1** -> AI trả lời chi tiết ✅.
   - Đổi sang `U03 (Dev)` -> Click **KB 1** -> AI thông báo bị chặn bảo mật 🔒.
4. **Thử nghiệm Kịch bản 2 (Bảng lương C-Level):**
   - Chọn nhân viên `U03 (Dev)` hoặc `U01 (HR L3)` -> Click **KB 2** -> AI thông báo bị chặn bảo mật 🔒.
5. **Thử nghiệm Kịch bản 3, 4, 5:**
   - Chọn bất kỳ nhân viên nào (`U01`, `U02`, `U03`) -> Quan sát AI phân biệt phiên bản 2025 (KB 3), tổng hợp kép (KB 4), và nhận diện giới hạn thiếu CSDL chấm công cá nhân (KB 5).

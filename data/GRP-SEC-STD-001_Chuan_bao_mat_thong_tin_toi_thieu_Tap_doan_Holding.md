---
id: "GRP-SEC-STD-001"
title: "Quy chuẩn bảo mật thông tin tối thiểu Tập đoàn Appota Holdings (Chuẩn bảo mật cấp Tập đoàn)"
version: 2.1
status: "ACTIVE"
governance_level: "GROUP_HOLDING_MANDATORY_STANDARD"
precedence_rule: "SUPERIOR_AUTHORITY_WINS (Cấp trên thắng cấp dưới)"
effective_date: "2025-01-01"
expiration_date: null
category: "Security & Access Control"
scope: "Áp dụng bắt buộc cho toàn bộ Công ty con, Công ty liên kết, Chi nhánh và tất cả phòng ban trực thuộc Tập đoàn"
jurisdiction: "Toàn cầu (Global Operations)"
contract_type: "Toàn bộ cán bộ nhân viên sử dụng hệ thống & thiết bị"
classification: "PUBLIC_INTERNAL"
author: "Ban Quản trị Rủi ro & An ninh Thông tin Tập đoàn (Group InfoSec & Risk Committee)"
approver: "Hội đồng Quản trị & Tổng Giám Đốc Tập đoàn (Group CEO)"
keywords:
  - "chuẩn bảo mật tập đoàn"
  - "holding baseline"
  - "2FA bắt buộc"
  - "cấm BYOD chưa kiểm duyệt"
  - "khóa màn hình 5 phút"
  - "cấp trên thắng cấp dưới"
  - "GRP-SEC-STD-001"
summary: "Quy chuẩn bảo mật thông tin tối thiểu cấp Tập đoàn có hiệu lực tối thượng (Superior Authority Wins): 2FA bắt buộc, quy định mật khẩu, cấm thiết bị cá nhân chưa kiểm soát, khóa màn hình tự động 5 phút."
---

# CHUẨN BẢO MẬT THÔNG TIN TỐI THIỂU TẬP ĐOÀN (GROUP SECURITY STANDARD)

> ⚡ **ĐIỀU KHOẢN HIỆU LỰC TỐI THƯỢNG (SUPREMACY CLAUSE / GROUP OVERRIDE):**  
> 1. Quy chuẩn này là **CHUẨN SÀN BẢO MẬT BẮT BUỘC (BASELINE MINIMUM STANDARD)** do Ban Lãnh đạo Tập đoàn ban hành với thẩm quyền cao nhất.  
> 2. **NGUYÊN TẮC CẤP TRÊN THẮNG CẤP DƯỚI (SUPERIOR RULE PREVAILS):**  
>    Mọi quy chế, chính sách nội bộ, hướng dẫn hoặc thỏa ước do bất kỳ Công ty con (Subsidiary), Công ty thành viên, Chi nhánh hay Phòng ban chức năng cấp dưới ban hành **TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP ĐẶT RA TIÊU CHUẨN THẤP HƠN HOẶC NỚI LỎNG HƠN** so với Quy chuẩn này.  
> 3. Trong mọi trường hợp có sự xung đột, mâu thuẫn hoặc diễn giải khác nhau giữa văn bản của công ty con và văn bản này, **QUY CHUẨN NÀY CỦA TẬP ĐOÀN LUÔN CÓ GIÁ TRỊ PHÁP LÝ ƯU TIÊN VÀ PHỦ QUYẾT TOÀN BỘ VĂN BẢN CẤP DƯỚI**.  
> 4. Mọi văn bản cấp dưới có nội dung giảm nhẹ tiêu chuẩn an toàn thông tin đều bị coi là **VÔ HIỆU TỪ THỜI ĐIỂM BAN HÀNH**.

> | THUỘC TÍNH QUY ĐỊNH (METADATA) | GIÁ TRỊ CHI TIẾT |
> | :--- | :--- |
> | **Mã văn bản (Document ID)** | `GRP-SEC-STD-001` |
> | **Tên văn bản (Title)** | Quy chuẩn bảo mật thông tin tối thiểu Tập đoàn Appota Holdings (Chuẩn bảo mật cấp Tập đoàn) |
> | **Phiên bản & Trạng thái** | Phiên bản 2.1 — **ACTIVE** |
> | **Ngày hiệu lực / Hết hạn** | Từ 2025-01-01 đến Vô thời hạn / Cho đến khi có văn bản thay thế |
> | **Phân loại bảo mật** | `PUBLIC_INTERNAL` |
> | **Phạm vi & Đối tượng** | Áp dụng bắt buộc cho toàn bộ Công ty con, Công ty liên kết, Chi nhánh và tất cả phòng ban trực thuộc Tập đoàn |
> | **Khu vực pháp lý (Jurisdiction)** | Toàn cầu (Global Operations) |
> | **Cơ quan ban hành & Phê duyệt** | Ban Quản trị Rủi ro & An ninh Thông tin Tập đoàn (Group InfoSec & Risk Committee) — Phê duyệt: Hội đồng Quản trị & Tổng Giám Đốc Tập đoàn (Group CEO) |
> | **Cấp thẩm quyền (Governance Level)** | GROUP_HOLDING_MANDATORY_STANDARD |
> | **Quy tắc ưu tiên (Precedence Rule)** | SUPERIOR_AUTHORITY_WINS (Cấp trên thắng cấp dưới) |
> | **Tóm tắt nội dung chính (RAG Summary)** | *Quy chuẩn bảo mật thông tin tối thiểu cấp Tập đoàn có hiệu lực tối thượng (Superior Authority Wins): 2FA bắt buộc, quy định mật khẩu, cấm thiết bị cá nhân chưa kiểm soát, khóa màn hình tự động 5 phút.* |

---

### ĐIỀU 1: CHUẨN XÁC THỰC ĐA YẾU TỐ BẮT BUỘC (MANDATORY MFA)
1. Toàn bộ tài khoản người dùng truy cập vào bất kỳ hệ thống nào của Tập đoàn (Email công ty, VPN, Slack, GitHub, Jira, ERP, AWS Console) **BẮT BUỘC PHẢI BẬT XÁC THỰC ĐA YẾU TỐ (MFA/2FA)**.
2. Phương thức MFA được chấp nhận: **Hardware Token (YubiKey) hoặc Time-based One-Time Password (TOTP) thông qua ứng dụng xác thực chuyên dụng (Google Authenticator, Microsoft Authenticator, 1Password)**.
3. **Nghiêm cấm tuyệt đối:** Không được sử dụng SMS OTP hoặc Email OTP làm kênh xác thực thứ hai do rủi ro bị tấn công SIM-swap và đánh chặn viễn thông.

### ĐIỀU 2: CHUẨN MẬT KHẨU VÀ CHU KỲ BẮT BUỘC ĐỔI MẬT KHẨU
1. **Độ dài và độ phức tạp:** Tối thiểu **12 ký tự**, bao gồm chữ hoa, chữ thường, chữ số và ít nhất một ký tự đặc biệt (!@#$%^&*).
2. **Chu kỳ đổi mật khẩu tối đa:** Mật khẩu tài khoản phải được hệ thống tự động ép buộc thay đổi **tối đa 90 ngày một lần**.
3. Không được đặt cấu hình cho phép nhân viên kéo dài chu kỳ đổi mật khẩu quá 90 ngày dưới bất kỳ hình thức nào. Hệ thống Identity Provider (Okta/Google Workspace) của các công ty con phải đồng bộ theo mốc này.

### ĐIỀU 3: QUẢN LÝ THIẾT BỊ ĐẦU CUỐI VÀ THIẾT BỊ LƯU TRỮ NGOÀI
1. **Mã hóa thiết bị:** 100% máy tính xách tay do công ty cấp hoặc máy tính cá nhân dùng làm việc (BYOD) phải được bật mã hóa toàn bộ ổ đĩa (BitLocker cho Windows, FileVault cho macOS).
2. **Kiểm soát cổng USB:** Toàn bộ cổng USB trên máy tính làm việc bị khóa ghi dữ liệu ra thiết bị lưu trữ ngoài (USB Drive, Thẻ nhớ SD, Ổ cứng di động) trừ khi có văn bản phê duyệt đặc cách của Giám đốc An ninh Thông tin Tập đoàn (CISO).

---
*Ban hành theo Nghị quyết số 04/2025/NQ-HĐQT Tập đoàn Appota Holdings.*

# HƯỚNG DẪN ĐÓNG GÓI & KHỞI CHẠY DỰ ÁN VỚI DOCKER
**Appota NextGen Enterprise Secure RAG System**

Tài liệu này hướng dẫn chi tiết cách đóng gói, cài đặt và khởi chạy toàn bộ hệ sinh thái (FastAPI Backend + Next.js Frontend + Qdrant Vector DB) bằng Docker trên bất kỳ máy tính nào (Windows, macOS, Linux).

---

## 1. YÊU CẦU TIỀN ĐỀ
- Đã cài đặt **Docker Desktop** (trên Windows/macOS) hoặc **Docker Engine + Docker Compose** (trên Linux).
  - Kiểm tra trong Terminal:
    ```bash
    docker --version
    docker compose version
    ```
- Một **Google Gemini API Key** miễn phí (lấy tại [Google AI Studio](https://aistudio.google.com/app/apikey)).

---

## 2. CÁC BƯỚC KHỞI CHẠY SIÊU TỐC (CHỈ 2 BƯỚC)

### Bước 1: Chuẩn bị file biến môi trường `.env`
Nhân bản file `.env.example` thành file `.env` ở thư mục gốc của dự án:
- Trên Linux / macOS / Git Bash:
  ```bash
  cp .env.example .env
  ```
- Trên Windows (PowerShell):
  ```powershell
  Copy-Item .env.example .env
  ```

Mở file `.env` và điền khóa API của bạn:
```env
GOOGLE_API_KEY="AIzaSyYourActualApiKeyHere..."
```

---

### Bước 2: Khởi chạy toàn bộ hệ thống bằng Docker Compose

Chạy lệnh sau tại thư mục gốc của dự án:

```bash
docker compose up --build -d
```

> **Giải thích tham số:**
> - `--build`: Tự động build Docker images cho Backend và Frontend.
> - `-d` (detached mode): Chạy ngầm trong background để không chiếm cửa sổ terminal.

---

## 3. TRUY CẬP VÀ TRẢI NGHIỆM

Sau khi Docker khởi động xong (khoảng 30–60 giây cho lần build đầu tiên):

| Dịch vụ | Địa chỉ truy cập | Mô tả |
| :--- | :--- | :--- |
| **Next.js Web Portal** | 👉 **[http://localhost:3000](http://localhost:3000)** | Giao diện tra cứu chính sách, ma trận phân quyền 5 kịch bản độc lập. |
| **FastAPI Swagger Docs** | 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)** | Tài liệu API tương tác trực tiếp (Swagger UI). |
| **API Health Check** | 👉 **[http://localhost:8000/api/health](http://localhost:8000/api/health)** | Kiểm tra trạng thái sẵn sàng của mô hình và database. |

---

## 4. CÁC LỆNH QUẢN LÝ DOCKER HỮU ÍCH

### Xem logs thời gian thực của toàn bộ hệ thống:
```bash
docker compose logs -f
```

### Xem logs riêng của Backend hoặc Frontend:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Kiểm tra trạng thái containers:
```bash
docker compose ps
```

### Tạm dừng hoặc khởi động lại:
```bash
# Tạm dừng:
docker compose stop

# Khởi động lại:
docker compose start

# Khởi động lại một service cụ thể:
docker compose restart backend
```

### Dừng và xóa containers (bảo toàn dữ liệu vector):
```bash
docker compose down
```

### Tái lập chỉ mục (Re-ingest) dữ liệu mới khi thay đổi tài liệu trong `data/`:
Bạn có 2 cách cực kỳ nhanh:
1. Bấm nút **"Re-index Documents"** trực tiếp trên Web UI (`http://localhost:3000`).
2. Hoặc thực thi script bên trong container:
   ```bash
   docker compose exec backend python reingest.py
   ```

---

## 5. CƠ CHẾ HOẠT ĐỘNG DOCKER TRONG DỰ ÁN

```mermaid
graph TD
    Client["Trình duyệt người dùng (Browser)"] -->|Cổng 3000| Frontend["Container: appota-rag-frontend (Next.js 16)"]
    Client -.->|Cổng 8000 / API Docs| Backend["Container: appota-rag-backend (FastAPI)"]
    Frontend -->|Mạng nội bộ Docker (http://backend:8000)| Backend
    Backend -->|Đọc/Ghi Mount| Qdrant[("./qdrant_db (Vector Store)")]
    Backend -->|Đọc Mount| Data[("./data (29 Markdown Policies)")]
    Backend -->|Cloud API| Gemini["Google Gemini API (LLM & Embeddings)"]
```

- **Tính di động (Portability):** Kho vector `qdrant_db/` đã được build sẵn và mount trực tiếp, giúp container backend khởi động **chỉ trong 1.5 giây** mà không tiêu tốn RAM hay cạn quota API.
- **Cách ly tài nguyên (Resource Isolation):** Cấu hình `OMP_NUM_THREADS=1` giúp container tiết kiệm RAM tối đa, chạy êm ái trên cả các máy tính cấu hình yếu (2GB - 4GB RAM).

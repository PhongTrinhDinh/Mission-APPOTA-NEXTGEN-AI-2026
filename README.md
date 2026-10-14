# Appota NextGen AI Talent 2026 - Enterprise Secure RAG System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid_Search-DC382D?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](DOCKER_GUIDE.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Tổng Quan Dự Án

**Appota NextGen Enterprise Secure RAG** là hệ thống trợ lý tra cứu văn bản quy chế và giải đáp chính sách doanh nghiệp thông minh, được xây dựng phục vụ công tác quản trị và tuân thủ nội bộ. Hệ thống cho phép nhân viên thuộc các khối phòng ban tra cứu quy định nội bộ, chế độ phúc lợi và quy trình vận hành với độ chính xác cao, đồng thời áp dụng cơ chế **Phân quyền Bảo mật Đa cấp (RBAC - Role-Based Access Control) ngay tại tầng Vector Database** để đảm bảo **cách ly dữ liệu tuyệt đối (Zero Data Leakage)** giữa các phòng ban và cấp bậc tổ chức.

---

## 🏛️ Sơ Đồ Kiến Trúc Hệ Thống

```mermaid
graph TD
    User["👤 Người dùng (Nhân viên / C-Level)"] -->|Cổng 3000| Client["Next.js 16 Web Client (React 19 + TypeScript)"]
    Client -->|API Proxy / Reverse Rewrite| API["FastAPI Backend (Cổng 8000)"]
    
    subgraph CoreRAG ["Hệ Thống Lõi Secure RAG"]
        API --> Auth["Xác thực User & Trích xuất Profile RBAC"]
        Auth --> HardFilter["Xây dựng Bộ lọc cứng RBAC Hard Filters"]
        
        HardFilter -->|DocLevel <= UserLevel & Dept hợp lệ| Qdrant[("Qdrant Vector DB (Hybrid Storage)")]
        
        Qdrant -->|Dense Cosine + Sparse BM25 (Top-15)| CandidateNodes["Danh sách đoạn trích ứng viên"]
        CandidateNodes --> FlashRank["FlashRank Reranker (ms-marco-MiniLM-L-12-v2)"]
        FlashRank --> TopNodes["Top 5 đoạn trích phù hợp nhất"]
    end
    
    subgraph CloudAI ["Tầng Mô Hình Đám Mây"]
        TopNodes --> GeminiLLM["Google Gemini (gemini-3.5-flash-lite)"]
        GeminiLLM --> FinalAnswer["Câu trả lời chuẩn xác + Nguồn trích dẫn + Điểm tin cậy"]
    end
    
    FinalAnswer --> Client
```

---

## 🌟 Điểm Nhấn Công Nghệ & Giải Quyết Vấn Đề

| Bài toán thực tế trong Doanh nghiệp | Giải pháp công nghệ của Appota NextGen RAG |
| :--- | :--- |
| **Rò rỉ dữ liệu mật chéo phòng ban:** RAG thông thường nạp chung mọi tài liệu vào context window của LLM, dễ làm lộ thang bảng lương quản lý cấp cao hoặc biên bản kỷ luật. | **RBAC Hard Filtering tại Vector DB:** Ngăn chặn và lọc bỏ tài liệu mật trực tiếp tại Qdrant ngay từ câu lệnh truy vấn Vector *trước khi* context được nạp vào LLM. |
| **Xung đột chính sách cũ & mới:** Các văn bản hết hiệu lực (ví dụ quy định chuyển phép năm 2022 vs 2025) dễ gây nhầm lẫn thông tin. | **Hybrid Search & FlashRank Reranker:** Kết hợp BM25 khớp chính xác từ khóa năm ban hành và Reranker đọc metadata `status: ACTIVE` để đưa văn bản mới nhất lên đầu. |
| **Tổng hợp đa tài liệu (Multi-Hop):** Một câu hỏi cần tổng hợp từ nhiều văn bản độc lập (ví dụ quy chế làm việc từ xa kết hợp trợ cấp thiết bị). | **Mở rộng Context & Rerank:** Cấu hình `RETRIEVAL_TOP_K = 15` kết hợp FlashRank cross-encoding, hỗ trợ Google Gemini tổng hợp đa tài liệu mạch lạc. |
| **Hỏi thông tin giao dịch cá nhân ngoài phạm vi RAG:** Hệ thống tài liệu tĩnh không lưu trữ lịch sử chấm công hay số dư phép thời gian thực. | **Safe Boundary Refusal:** Mô hình nhận diện giới hạn nghiệp vụ, từ chối an toàn (không bịa đặt số liệu) và hướng dẫn người dùng tới cổng HRM nội bộ. |

---

## 🧪 5 Kịch Bản Kiểm Thử Độc Lập Phân Quyền (Cross-User RBAC Matrix)

Dự án thiết kế **5 kịch bản kiểm thử nghiệp vụ độc lập với người dùng** nhằm chứng minh năng lực phân quyền đa chiều (báo cáo phân tích chuyên sâu tại [TEST_SCENARIOS.md](TEST_SCENARIOS.md)):

| Mã KB | Tên Kịch Bản | Câu Hỏi Chuẩn Hóa | `U02` - Sales (L1) | `U03` - Dev (L1) | `U01` - HR (L3) | `U99` - BOD / C-Level (L4/5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KB-01** | **Chính sách hoa hồng Sales** *(Cô lập phòng ban)* | *"Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"* | ✅ **Xem được**<br>(Đúng phòng Sales) | 🔒 **Bị chặn RBAC**<br>(Khác phòng ban) | 🔒 **Bị chặn RBAC**<br>(Khác phòng ban) | ✅ **Xem được**<br>(C-Level xem toàn bộ) |
| **KB-02** | **Bảng lương mật C-Level** *(Bảo mật cấp bậc)* | *"Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"* | 🔒 **Bị chặn RBAC**<br>(Level 1 < Level 4) | 🔒 **Bị chặn RBAC**<br>(Level 1 < Level 4) | 🔒 **Bị chặn RBAC**<br>(Level 3 < Level 4) | ✅ **Xem được**<br>(Level ≥ 4 hợp lệ) |
| **KB-03** | **Xung đột chuyển phép** *(Đa bản 2022 vs 2025)* | *"Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"* | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) |
| **KB-04** | **Remote & Thiết bị** *(Tổng hợp đa nguồn)* | *"Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"* | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) | ✅ **Xem được**<br>(Chính sách chung) |
| **KB-05** | **Số dư phép cá nhân** *(Giới hạn an toàn)* | *"Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"* | ⚠️ **Từ chối an toàn**<br>(Chưa nối CSDL HRM) | ⚠️ **Từ chối an toàn**<br>(Chưa nối CSDL HRM) | ⚠️ **Từ chối an toàn**<br>(Chưa nối CSDL HRM) | ⚠️ **Từ chối an toàn**<br>(Chưa nối CSDL HRM) |

---

## ⚠️ Nguyên nhân không thể deploy

Sản phẩm được phát triển ưu tiên deploy miễn phí trên các nền tảng, công cụ hỗ trợ deploy sản phẩm, tuy nhiên khi thử nghiệm thực tế thì không thể deploy thành công ở các gói miễn phí.

---

## ⚡ Khởi Chạy Nhanh Với Docker (Khuyên Dùng)

Bạn có thể khởi chạy toàn bộ hệ thống (FastAPI Backend + Next.js Frontend + Qdrant Vector DB có sẵn) chỉ bằng **1 lệnh duy nhất** trên bất kỳ máy tính nào:

```bash
# 1. Clone repository
git clone https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026.git
cd Mission-APPOTA-NEXTGEN-AI-2026

# 2. Tạo file cấu hình .env từ mẫu
cp .env.example .env
# Mở file .env và điền khóa GOOGLE_API_KEY="AIzaSy..."

# 3. Khởi chạy toàn bộ hệ thống bằng Docker Compose
docker compose up --build -d
```

### Địa chỉ truy cập:
* 🌐 **Next.js Web Portal:** 👉 **[http://localhost:3000](http://localhost:3000)**
* 📖 **Tài liệu API Swagger:** 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**
* 🩺 **API Health Check:** 👉 **[http://localhost:8000/api/health](http://localhost:8000/api/health)**

*(Xem hướng dẫn chi tiết các lệnh quản lý container, logs và cấu hình tại [DOCKER_GUIDE.md](DOCKER_GUIDE.md)).*

---

## 💻 Cài Đặt Thủ Công Trên Máy (Local Manual Setup)

### Yêu cầu môi trường
* **Python 3.10+** (Khuyên dùng Python 3.12)
* **Node.js 18+** & **npm**

### Bước 1: Thiết lập Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 2: Cài đặt thư viện Backend
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` từ `.env.example`:
```bash
# Windows
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
Điền Google Gemini API Key của bạn vào `.env`:
```env
GOOGLE_API_KEY="your-google-gemini-api-key"
LLM_MODEL="gemini-3.5-flash-lite"
EMBEDDING_MODEL="text-embedding-004"
```

### Bước 4: Khởi chạy Fullstack bằng 1 lệnh
Chạy file điều phối tự động:
```bash
python main.py
```
*(Nếu muốn chạy riêng lẻ từng dịch vụ: `python main.py -b` cho Backend hoặc `python main.py -f` cho Frontend).*

---

## 🧪 Chạy Bộ Kiểm Thử Tự Động (Automated Testing)

Chạy toàn bộ 67 bài test kiểm thử tự động (bao gồm 10 tests kịch bản phân quyền chéo RBAC):
```bash
pytest tests/ -v
```

Hoặc chỉ chạy riêng 5 kịch bản phân quyền:
```bash
pytest tests/test_scenarios.py -v
```

---

## 📁 Cấu Trúc Thư Mục Dự Án (Project Structure)

```text
├── data/                       # 29 tài liệu Markdown quy chế doanh nghiệp chuẩn hóa kèm YAML frontmatter
├── qdrant_db/                  # Cơ sở dữ liệu Qdrant Hybrid (Dense 768 + Sparse BM25) lưu trữ sẵn
├── src/                        # Mã nguồn lõi hệ thống RAG Backend
│   ├── api/                    # FastAPI routes, Pydantic schemas và dependencies
│   ├── config.py               # Cấu hình tập trung hệ thống
│   ├── models.py               # Khởi tạo Google Gemini LLM & GenAI Embeddings
│   ├── rag_engine.py           # SecureRAGEngine với RBAC Hard Filtering & xử lý phản hồi
│   ├── reranker.py             # FlashRank cross-encoder reranking integration
│   ├── user_manager.py         # Quản lý tài khoản và phân quyền người dùng
│   └── vector_store.py         # Quản trị Qdrant Vector Store & Ingestion pipeline
├── frontend/                   # Ứng dụng Next.js 16 Web Portal
│   ├── app/                    # Next.js App Router (Giao diện chính, API proxy)
│   ├── lib/                    # API client kết nối Backend
│   └── package.json            # Dependencies Frontend (React 19, TypeScript)
├── tests/                      # Bộ kiểm thử tự động (Pytest)
│   ├── test_scenarios.py       # Kiểm thử 5 kịch bản RBAC độc lập
│   ├── test_api.py             # Kiểm thử các endpoint FastAPI
│   ├── test_rag_engine.py      # Kiểm thử thuật toán phân quyền lọc cứng
│   └── ...
├── app.py                      # FastAPI Application entrypoint & vòng đời khởi động
├── main.py                     # Trình khởi chạy Fullstack hợp nhất
├── reingest.py                 # Script lập lại chỉ mục vector độc lập
├── users.json                  # CSDL người dùng mẫu đại diện các cấp bậc (L1 - L5)
├── requirements.txt            # Thư viện Python phụ thuộc
├── Dockerfile.backend          # Dockerfile đóng gói Backend FastAPI siêu nhẹ
├── docker-compose.yml          # Điều phối đa container Backend + Frontend
├── DOCKER_GUIDE.md             # Cẩm nang hướng dẫn Docker toàn diện
├── TEST_SCENARIOS.md           # Báo cáo phân tích chuyên sâu 5 kịch bản kiểm thử
└── README.md                   # Tài liệu hướng dẫn chính của dự án
```

---

## 📦 Các Gói & Công Nghệ Sử Dụng (Packages Used)

### Kiến Trúc Backend
* **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/) xây dựng RESTful API bất đồng bộ hiệu năng cao.
* **RAG Orchestration:** [LlamaIndex Core](https://www.llamaindex.ai/) quản lý tài liệu, vector index và tổng hợp câu trả lời.
* **Vector Database:** [Qdrant Client](https://github.com/qdrant/qdrant-client) cung cấp kho lưu trữ nhúng Hybrid (Dense Vector + BM25 Sparse Index).
* **Sparse Embedding:** [FastEmbed](https://github.com/qdrant/fastembed) tính toán vector BM25 tức thì trên CPU.
* **Reranking Engine:** [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) (`ms-marco-MiniLM-L-12-v2`) chấm điểm chéo siêu nhẹ và độ trễ thấp.
* **Dense Embedding:** [Google GenAI Embeddings](https://ai.google.dev/) (`gemini-embedding-2` / `text-embedding-004`, 768-dim) biểu diễn ngữ nghĩa chính xác cao.
* **LLM Integration:** [llama-index-llms-google-genai](https://developers.google.com/gemini) kết nối Google Gemini (`gemini-3.5-flash-lite`).
* **Testing:** [Pytest](https://docs.pytest.org/) & [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/).

### Kiến Trúc Frontend
* **Framework:** [Next.js 16](https://nextjs.org/) (App Router, React 19).
* **Ngôn ngữ:** [TypeScript](https://www.typescriptlang.org/) đảm bảo an toàn kiểu dữ liệu end-to-end.
* **Giao diện:** Vanilla CSS hiện đại, thiết kế Responsive, hiệu ứng Glassmorphism và bảng màu Dark Mode cao cấp.

---

## 🤝 Đóng Góp & Hỗ Trợ (Community & Support)

Mọi đóng góp, báo cáo lỗi và đề xuất nâng cấp tính năng đều được hoan nghênh:
* **Đặt câu hỏi & Thảo luận:** Mở bài viết tại [GitHub Discussions](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/discussions).
* **Báo cáo lỗi (Issues):** Mở ticket tại [GitHub Issues](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/issues).
* **Pull Requests:** Tạo nhánh mới từ `main` và gửi PR để chúng tôi cùng đánh giá.

# Appota NextGen AI Talent 2026 - Enterprise Secure RAG System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid_Search-DC382D?logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](DOCKER_GUIDE.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Project Overview

**Appota NextGen Enterprise Secure RAG** is an intelligent internal policy search and question-answering system built for enterprise governance and compliance. It empowers employees across diverse business units to search corporate regulations, benefits, and operational guidelines with precision, while strictly enforcing **multi-level Role-Based Access Control (RBAC) directly inside the vector database** to guarantee **Zero Data Leakage** between departments and organizational ranks.

---

## 🏛️ System Architecture

```mermaid
graph TD
    User(["👤 Enterprise User (Staff / Manager / C-Level)"]) -->|Port 3000| Client["Next.js 16 Web Client (React 19 + TypeScript)"]
    Client -->|API Proxy / Reverse Rewrite| API["FastAPI Backend (Port 8000)"]
    
    subgraph Security_and_Retrieval ["Secure RAG Core Pipeline"]
        API --> Auth["User Authentication & Profile Extraction (RBAC Context)"]
        Auth --> HardFilter["Dynamic RBAC Hard Filter Construction"]
        
        HardFilter -->|Level <= UserLevel AND Dept in [UserDept, ALL]| Qdrant[("Qdrant Vector DB (Hybrid Storage)")]
        
        Qdrant -->|Dense Cosine + Sparse BM25 Top-15 Chunks| CandidateNodes["Candidate Retrieved Passages"]
        CandidateNodes --> FlashRank["FlashRank Reranker (ms-marco-MiniLM-L-12-v2)"]
        FlashRank --> TopNodes["Top 5 High-Relevance Chunks"]
    end
    
    subgraph Generative_AI ["Cloud Generative AI Layer"]
        TopNodes --> GeminiLLM["Google Gemini (gemini-3.5-flash-lite)"]
        GeminiLLM --> FinalAnswer["Synthesized Answer + Source Document Citations + Relevance Scores"]
    end
    
    FinalAnswer --> Client
```

---

## 🌟 Key Problems Solved & Technical Innovations

| Enterprise Challenge | Solution in Appota NextGen Secure RAG |
| :--- | :--- |
| **Unauthorized Data Leakage:** Traditional RAG models load all documents into the LLM context, inadvertently exposing sensitive executive payroll or disciplinary actions to unauthorized staff. | **Deterministic RBAC Hard Filtering at Vector DB:** Access control is applied as hard metadata filters directly in Qdrant *before* retrieval, ensuring unauthorized vectors never reach the LLM context. |
| **Conflicting Policy Versions:** Outdated regulations (e.g., 2022 vs. 2025 leave transfer limits) frequently confuse retrieval algorithms. | **Hybrid Search + FlashRank Reranker:** Combines exact BM25 keyword matching with FlashRank reranking that evaluates `status: ACTIVE` metadata, prioritizing active policies over superseded versions. |
| **Multi-Source Synthesis:** Complex questions (e.g., remote work policy combined with home office equipment stipends) require synthesizing multiple independent documents. | **Expanded Multi-Hop Context:** Configured with `RETRIEVAL_TOP_K = 15` and FlashRank cross-encoding, allowing Google Gemini to assemble cohesive, multi-part answers. |
| **Personal Real-Time Queries:** Employees asking for real-time leave balances or time-tracking transactions that do not exist in static Markdown policy manuals. | **Safe Boundary Refusal:** The model recognizes domain boundaries, safely refuses to hallucinate specific quantitative personal balances, and directs users to the internal HRM portal. |

---

## 🧪 5 Standardized Testing Scenarios (Cross-User RBAC Matrix)

The system features **5 standardized business test scenarios** designed to verify access isolation across 4 representative organizational roles (see detailed report in [TEST_SCENARIOS.md](TEST_SCENARIOS.md)):

| Scenario ID | Business Case | Standardized Query | `U02` - Sales (L1) | `U03` - Dev (L1) | `U01` - HR Mgr (L3) | `U99` - BOD / C-Level (L4/5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KB-01** | **Sales Commission Policy** *(Department Isolation)* | *"Chính sách hoa hồng bán hàng và cơ chế tính thưởng doanh số của khối Kinh doanh (Sales) được quy định như thế nào?"* | ✅ **ACCESSIBLE**<br>(Same department) | 🔒 **BLOCKED RBAC**<br>(Cross-department) | 🔒 **BLOCKED RBAC**<br>(Cross-department) | ✅ **ACCESSIBLE**<br>(Full cross-dept access) |
| **KB-02** | **C-Level Executive Payroll** *(Clearance Level Isolation)* | *"Quy định về khung thang bảng lương cấp quản lý cấp cao (C-Level/Director) và quy trình xử lý kỷ luật sa thải đặc biệt?"* | 🔒 **BLOCKED RBAC**<br>(Level 1 < Level 4) | 🔒 **BLOCKED RBAC**<br>(Level 1 < Level 4) | 🔒 **BLOCKED RBAC**<br>(Level 3 < Level 4) | ✅ **ACCESSIBLE**<br>(Level ≥ 4 authorized) |
| **KB-03** | **Leave Rollover Conflict** *(Multi-Version: 2022 vs 2025)* | *"Theo quy định hiện hành của công ty, số ngày nghỉ phép năm tối đa được phép chuyển sang năm sau là bao nhiêu ngày và hạn chót sử dụng là khi nào?"* | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) |
| **KB-04** | **Remote Work & Equipment** *(Multi-Source Synthesis)* | *"Quy định về chế độ làm việc từ xa (Remote/Hybrid) và định mức hỗ trợ trang thiết bị làm việc tại nhà được áp dụng như thế nào?"* | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) | ✅ **ACCESSIBLE**<br>(General policy) |
| **KB-05** | **Personal Leave Balance** *(Safe Boundary Refusal)* | *"Tính đến hôm nay, cá nhân tôi còn lại chính xác bao nhiêu ngày nghỉ phép chưa sử dụng trong năm nay và đã nộp đơn nghỉ vào những ngày nào?"* | ⚠️ **SAFE REFUSAL**<br>(HRM DB unlinked) | ⚠️ **SAFE REFUSAL**<br>(HRM DB unlinked) | ⚠️ **SAFE REFUSAL**<br>(HRM DB unlinked) | ⚠️ **SAFE REFUSAL**<br>(HRM DB unlinked) |

---

## ⚡ Quick Start with Docker (Recommended)

You can launch the entire ecosystem (FastAPI Backend + Next.js Frontend + Pre-built Qdrant Vector DB) with a **single command** on any device running Docker:

```bash
# 1. Clone repository
git clone https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026.git
cd Mission-APPOTA-NEXTGEN-AI-2026

# 2. Setup environment configuration
cp .env.example .env
# Open .env and add your GOOGLE_API_KEY="AIzaSy..."

# 3. Start fullstack services with Docker Compose
docker compose up --build -d
```

### Access Endpoints:
* 🌐 **Next.js Web Portal:** 👉 **[http://localhost:3000](http://localhost:3000)**
* 📖 **Interactive Swagger API Docs:** 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**
* 🩺 **Backend Health Check:** 👉 **[http://localhost:8000/api/health](http://localhost:8000/api/health)**

*(For comprehensive container management commands and configuration details, refer to [DOCKER_GUIDE.md](DOCKER_GUIDE.md)).*

---

## 💻 Manual Local Installation (Without Docker)

### Prerequisites
* **Python 3.10+** (Python 3.12 recommended)
* **Node.js 18+** & **npm**

### Step 1: Set Up Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create your `.env` file from `.env.example`:
```bash
# Windows
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
Fill in your Google Gemini API key:
```env
GOOGLE_API_KEY="your-google-gemini-api-key"
LLM_MODEL="gemini-3.5-flash-lite"
EMBEDDING_MODEL="text-embedding-004"
```

### Step 4: Launch Fullstack Application
Start both the FastAPI backend and Next.js frontend with the unified runner:
```bash
python main.py
```
*(Use `python main.py -b` for backend only, or `python main.py -f` for frontend only).*

---

## 🧪 Automated Testing & Verification

Run the complete test suite (67 unit and integration tests, including cross-user RBAC security matrix validation):
```bash
pytest tests/ -v
```

To run only the 5 business scenario tests:
```bash
pytest tests/test_scenarios.py -v
```

---

## 📁 Repository Directory Structure

```text
├── data/                       # 29 standardized Markdown corporate policies with YAML frontmatter
├── qdrant_db/                  # Pre-indexed Qdrant Hybrid Vector DB (Dense 768 + Sparse BM25)
├── src/                        # Core RAG Backend implementation
│   ├── api/                    # FastAPI routes, Pydantic schemas, and dependencies
│   ├── config.py               # Centralized configuration management
│   ├── models.py               # Google Gemini LLM & GenAI Embeddings integration
│   ├── rag_engine.py           # SecureRAGEngine with RBAC Hard Filtering & response synthesis
│   ├── reranker.py             # FlashRank cross-encoder reranking integration
│   ├── user_manager.py         # Authentication and user permission management
│   └── vector_store.py         # Qdrant Vector Store management & ingestion pipeline
├── frontend/                   # Next.js 16 Web Portal
│   ├── app/                    # Next.js App Router (UI, API proxy handlers)
│   ├── lib/                    # API client connecting to backend
│   └── package.json            # Frontend dependencies (React 19, TypeScript)
├── tests/                      # Automated test suite (Pytest)
│   ├── test_scenarios.py       # Cross-user RBAC matrix validation for 5 scenarios
│   ├── test_api.py             # FastAPI endpoint verification
│   ├── test_rag_engine.py      # Hard filtering unit tests
│   └── ...
├── app.py                      # FastAPI Application entrypoint & lifespan lifecycle
├── main.py                     # Unified fullstack process launcher
├── reingest.py                 # Standalone vector re-indexing script
├── users.json                  # Mock enterprise user directory (Level 1 to Level 5)
├── requirements.txt            # Python dependencies
├── Dockerfile.backend          # Lightweight FastAPI Python 3.12 container
├── docker-compose.yml          # Multi-container orchestration (Backend + Frontend)
├── DOCKER_GUIDE.md             # Comprehensive Docker deployment manual
├── TEST_SCENARIOS.md           # In-depth 5-scenario evaluation and testing report
└── README.md                   # Main project documentation
```

---

## 📦 Packages & Technologies Used

### Backend Architecture
* **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/) for high-throughput asynchronous REST APIs.
* **RAG Orchestration:** [LlamaIndex Core](https://www.llamaindex.ai/) for document abstraction, vector indexing, and synthesis.
* **Vector Database:** [Qdrant Client](https://github.com/qdrant/qdrant-client) providing embedded hybrid storage (Dense Vector + BM25 Sparse Index).
* **Sparse Embedding:** [FastEmbed](https://github.com/qdrant/fastembed) for on-the-fly BM25 vector computation.
* **Reranking Engine:** [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) (`ms-marco-MiniLM-L-12-v2`) for ultra-low latency reranking.
* **Dense Embedding:** [Google GenAI Embeddings](https://ai.google.dev/) (`gemini-embedding-2` / `text-embedding-004`, 768-dim) for high-precision semantic search.
* **LLM Integration:** [llama-index-llms-google-genai](https://developers.google.com/gemini) connecting to Google Gemini (`gemini-3.5-flash-lite`).
* **Testing:** [Pytest](https://docs.pytest.org/) & [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/).

### Frontend Architecture
* **Framework:** [Next.js 16](https://nextjs.org/) (App Router, React 19).
* **Language:** [TypeScript](https://www.typescriptlang.org/) for end-to-end type safety.
* **Styling:** Modular Vanilla CSS with responsive design, glassmorphism aesthetics, and dark mode palette.

---

## 🤝 Community & Support

Feedback, issue reports, and contributions are warmly welcome:
* **Discussions:** Start a conversation on [GitHub Discussions](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/discussions).
* **Bug Reports & Feature Requests:** File an issue on [GitHub Issues](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/issues).
* **Pull Requests:** Fork the repository, create a branch, and submit a PR for review.

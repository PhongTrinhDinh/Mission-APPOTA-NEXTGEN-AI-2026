---
title: Appota NextGen AI RAG Backend
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
---

# Appota NextGen AI Talent 2026 - Enterprise Secure RAG System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Hybrid_Search-red.svg)](https://qdrant.tech/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

**Appota NextGen Enterprise Secure RAG** is an intelligent internal policy search and question-answering system built for enterprise governance. It enables employees across different departments to search corporate regulations, benefits, and operational guidelines with precision, while strictly enforcing multi-level Role-Based Access Control (RBAC) directly inside the vector database to guarantee zero data leakage between departments and organizational ranks.

---

## Highlights

### The Problems It Solves
* **Unauthorized Data Leakage:** Standard RAG pipelines ingest all enterprise documents indiscriminately into LLM context windows, accidentally exposing sensitive compensation bands, executive disciplinary records, or department-only playbooks to unauthorized staff.
* **Conflicting Policy Versions:** Corporate environments frequently update policies over time (e.g., 2022 vs. 2025 leave regulations). Without semantic recency scoring and reranking, naive search often retrieves superseded rules.
* **Information Fragmentation:** Answering single employee inquiries (e.g., remote work equipment allowances) often requires cross-referencing multiple separate policies across HR, IT, and Finance.

### Core Features Explained Simply
* **Deterministic RBAC Hard Filtering:** Access control is enforced at the database level before retrieval. If an Engineering employee asks about Sales commissions or executive compensation, unauthorized documents are filtered out prior to LLM reasoning.
* **Hybrid Search (Dense + Sparse BM25):** Combines semantic vector understanding (`intfloat/multilingual-e5-large`) with exact keyword matching (`Qdrant/bm25`), ensuring accurate document retrieval for both conceptual queries and exact policy code references.
* **Ultra-Fast FlashRank Reranker:** Uses a lightweight `ms-marco-MiniLM-L-12-v2` cross-encoder to rescore candidate passages, pushing the most pertinent clauses to the top of the context window.
* **Context-Grounded Reasoning:** Powered by Google Gemini (`gemini-3.5-flash-lite`), generating clear, helpful answers with verifiable source document citations and refusal prompts for out-of-domain personal inquiries.

---

## Usage

When launching the application, you are greeted with a clean, modern web interface:

1. **Select an Employee Persona:** Choose from pre-configured enterprise profiles—such as an Engineering Developer (Level 1), a Sales Representative (Level 1), an HR Manager (Level 2), or a Board Member / CEO (Level 4).
2. **Ask a Policy Question:** Type any workplace inquiry in natural Vietnamese or English (e.g., *"How is the annual leave rollover calculated under current regulations?"* or *"What is the sales bonus structure?"*).
3. **Receive a Secure, Cited Answer:**
   * **Authorized users** instantly receive a concise, synthesized answer alongside interactive cards showing the exact source policies, clearance levels, and relevance scores.
   * **Unauthorized users** asking cross-department or high-clearance queries receive a polite, safe boundary message explaining that the information is outside their access scope.

---

## Packages Used

### Backend Architecture
* **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/) for high-throughput asynchronous REST APIs.
* **RAG Orchestration:** [LlamaIndex Core](https://www.llamaindex.ai/) for document abstraction, vector indexing, and synthesis.
* **Vector Database:** [Qdrant Client](https://github.com/qdrant/qdrant-client) providing local embedded hybrid storage (Dense Vector + BM25 Sparse Index).
* **Sparse Embedding:** [FastEmbed](https://github.com/qdrant/fastembed) for on-the-fly BM25 generation.
* **Reranking Engine:** [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) for ultra-low latency CPU/GPU reranking.
* **Dense Embedding:** [HuggingFace Transformers](https://huggingface.co/) & [PyTorch](https://pytorch.org/) running `multilingual-e5-large` with CUDA GPU acceleration.
* **LLM Integration:** [llama-index-llms-google-genai](https://developers.google.com/gemini) connecting to Google Gemini.
* **Testing:** [Pytest](https://docs.pytest.org/) & [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/) with comprehensive scenario coverage.

### Frontend Architecture
* **Framework:** [Next.js 16](https://nextjs.org/) (App Router, React 19).
* **Language:** [TypeScript](https://www.typescriptlang.org/) for end-to-end type safety.
* **Styling:** Modular Vanilla CSS with responsive design, glassmorphism aesthetics, and dark mode palette.

---

## Installation

### Prerequisites
* **Python 3.10+** (Python 3.12 recommended)
* **Node.js 18+** & **npm**
* *(Optional)* NVIDIA GPU with CUDA support for accelerated local embeddings.

### Step 1: Clone the Repository
```bash
git clone https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026.git
cd Mission-APPOTA-NEXTGEN-AI-2026
```

### Step 2: Setup Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the sample environment file and add your Google Gemini API key:
```bash
# Windows
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
Open `.env` and set your key:
```env
GOOGLE_API_KEY="your-google-gemini-api-key"
LLM_MODEL="gemini-3.5-flash-lite"
```

### Step 5: Ingest Documents & Build Vector Index
Initialize the Qdrant Hybrid Collection from markdown files in `data/`:
```bash
python reingest.py
```

### Step 6: Start the Fullstack Application
Run both the FastAPI Backend and Next.js Frontend with a single command:
```bash
python main.py
```

* **Web UI:** [http://localhost:3000](http://localhost:3000)
* **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
* **Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

*(To run individual services, use `python main.py -b` for backend only, or `python main.py -f` for frontend only).*

### Step 7: Run Automated Verification Tests
Validate the 5 cross-user RBAC security scenarios:
```bash
pytest tests/test_scenarios.py -v
```

---

## Feedback and Contribution

We welcome feedback, suggestions, and community contributions!

* **Questions & Discussions:** Join the conversation on our [GitHub Discussions](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/discussions) tab to share ideas or ask for guidance.
* **Bug Reports & Feature Requests:** Please open an issue on the [GitHub Issues](https://github.com/PhongTrinhDinh/Mission-APPOTA-NEXTGEN-AI-2026/issues) page with a clear description and reproduction steps.
* **Pull Requests:** Feel free to fork the repository, create a feature branch, and submit a PR for review.

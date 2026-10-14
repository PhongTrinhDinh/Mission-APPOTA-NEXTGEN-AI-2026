import os
import torch
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from src.config import Config

def setup_global_models():
    """Khởi tạo toàn cục mô hình Google Gemini LLM và mô hình Embedding Local (Nvidia GPU/CPU)."""
    if not Config.GOOGLE_API_KEY and os.getenv("TESTING", "").lower() in ("1", "true"):
        from llama_index.core.llms.mock import MockLLM
        Settings.llm = MockLLM()
    else:

        print(f"[Models] Khởi tạo mô hình Google Gemini '{Config.LLM_MODEL}'...")
        Settings.llm = GoogleGenAI(
            model=Config.LLM_MODEL,
            api_key=Config.GOOGLE_API_KEY,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_NEW_TOKENS
        )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    local_dir = getattr(Config, "LOCAL_MODEL_DIR", "./local_model")
    print(f"[Embedding] Nạp mô hình local '{Config.EMBEDDING_MODEL}' từ '{local_dir}' trên thiết bị: {device.upper()}...")
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=Config.EMBEDDING_MODEL,
        cache_folder=local_dir,
        device=device
    )
    print(f"[Models] ✅ Mô hình đã sẵn sàng (Embedding Local hoạt động trên {device.upper()})!")

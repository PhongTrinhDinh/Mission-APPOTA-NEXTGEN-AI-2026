import os
from llama_index.core import Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from src.config import Config

def setup_global_models():
    """Khởi tạo toàn cục mô hình Google Gemini LLM và Google GenAI Embedding."""
    if not Config.GOOGLE_API_KEY and os.getenv("TESTING", "").lower() in ("1", "true"):
        from llama_index.core.llms.mock import MockLLM
        from llama_index.core.embeddings import MockEmbedding
        Settings.llm = MockLLM()
        Settings.embed_model = MockEmbedding(embed_dim=768)
    else:
        print(f"[Models] Khởi tạo mô hình Google Gemini '{Config.LLM_MODEL}'...")
        Settings.llm = GoogleGenAI(
            model=Config.LLM_MODEL,
            api_key=Config.GOOGLE_API_KEY,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_NEW_TOKENS
        )
        target_model = Config.EMBEDDING_MODEL
        if target_model in ("text-embedding-004", "models/text-embedding-004"):
            target_model = "gemini-embedding-001"

        try:
            from google.genai import types
            embed_cfg = types.EmbedContentConfig(output_dimensionality=768)
        except Exception:
            embed_cfg = None

        print(f"[Embedding] Khởi tạo mô hình Google GenAI Embedding '{Config.EMBEDDING_MODEL}' (dim=768)...")
        Settings.embed_model = GoogleGenAIEmbedding(
            model_name=target_model,
            api_key=Config.GOOGLE_API_KEY,
            embedding_config=embed_cfg,
            embed_batch_size=32,
            retries=6,
            retry_min_seconds=4.0,
            retry_max_seconds=60.0
        )
    print("[Models] ✅ Mô hình đã sẵn sàng (Google Gemini LLM & GenAI Embedding)!")

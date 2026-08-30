from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    docs_dir: Path = ROOT / "docs"
    model_provider: str = os.getenv("MODEL_PROVIDER", "openai").lower()
    index_dir: Path = ROOT / os.getenv(
        "RAG_INDEX_DIR",
        ".rag_index_ollama" if os.getenv("MODEL_PROVIDER", "openai").lower() == "ollama" else ".rag_index",
    )
    collection_name: str = "enterprise_documents"
    chat_model: str = os.getenv(
        "OLLAMA_CHAT_MODEL" if os.getenv("MODEL_PROVIDER", "openai").lower() == "ollama" else "OPENAI_CHAT_MODEL",
        "llama3.2:3b" if os.getenv("MODEL_PROVIDER", "openai").lower() == "ollama" else "gpt-4.1-mini",
    )
    embedding_model: str = os.getenv(
        "OLLAMA_EMBEDDING_MODEL" if os.getenv("MODEL_PROVIDER", "openai").lower() == "ollama" else "OPENAI_EMBEDDING_MODEL",
        "nomic-embed-text" if os.getenv("MODEL_PROVIDER", "openai").lower() == "ollama" else "text-embedding-3-small",
    )
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_k: int = 5


settings = Settings()

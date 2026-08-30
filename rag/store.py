from __future__ import annotations

import os
import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from .config import Settings


class KnowledgeBase:
    def __init__(self, cfg: Settings):
        if cfg.model_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        self.cfg = cfg
        if cfg.model_provider == "ollama":
            self.embeddings = OllamaEmbeddings(model=cfg.embedding_model, base_url=cfg.ollama_base_url)
        else:
            self.embeddings = OpenAIEmbeddings(model=cfg.embedding_model)

    def vector_store(self) -> Chroma:
        return Chroma(collection_name=self.cfg.collection_name, embedding_function=self.embeddings,
                      persist_directory=str(self.cfg.index_dir))

    def add(self, documents: list[Document]) -> int:
        if not documents:
            return 0
        store = self.vector_store()
        store.add_documents(documents, ids=[doc.metadata["id"] for doc in documents])
        return len(documents)

    def search(self, query: str, category: str = "auto") -> list[Document]:
        filter_value = {"category": category} if category in {"hr", "technical", "compliance"} else None
        return self.vector_store().similarity_search(query, k=self.cfg.retrieval_k, filter=filter_value)

    def count(self) -> int:
        if not self.cfg.index_dir.exists():
            return 0
        return self.vector_store()._collection.count()

    def reset(self) -> None:
        if self.cfg.index_dir.exists():
            shutil.rmtree(self.cfg.index_dir)

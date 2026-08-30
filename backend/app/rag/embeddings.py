"""
Embedding provider abstraction.

Backed by Gemini's `gemini-embedding-001` model (the successor to the
retired `text-embedding-004`, which Google shut down Jan 14, 2026).

IMPORTANT: output_dimensionality must be passed to embed_query()/
embed_documents() directly, NOT to the GoogleGenerativeAIEmbeddings
constructor - the constructor silently ignores it in current versions
of langchain-google-genai and returns the model's default 3072-dim
vectors regardless, breaking any Pinecone index created with a smaller
fixed dimension.
"""
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings


@lru_cache
def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )


def embed_text(text: str) -> list[float]:
    return get_embedding_model().embed_query(
        text, output_dimensionality=settings.EMBEDDING_DIMENSIONS
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedding_model().embed_documents(
        texts, output_dimensionality=settings.EMBEDDING_DIMENSIONS
    )

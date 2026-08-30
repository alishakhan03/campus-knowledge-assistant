"""
VectorStoreService: the ONLY place in the app that talks to Pinecone directly.

Everything else (rag_service, document_service) goes through this class so
Pinecone could be swapped for another vector DB later with minimal blast radius.
"""
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.rag.embeddings import embed_text, embed_texts


class VectorStoreService:
    def __init__(self) -> None:
        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index_name = settings.PINECONE_INDEX_NAME
        self._namespace = settings.PINECONE_NAMESPACE
        self._ensure_index()
        self._index = self._pc.Index(self._index_name)

    def _ensure_index(self) -> None:
        existing = [idx["name"] for idx in self._pc.list_indexes()]
        if self._index_name not in existing:
            self._pc.create_index(
                name=self._index_name,
                dimension=settings.EMBEDDING_DIMENSIONS,
                metric="cosine",
                spec=ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION),
            )

    def health_check(self) -> bool:
        try:
            self._pc.describe_index(self._index_name)
            return True
        except Exception:
            return False

    def add_document_chunks(self, document_id: int, document_title: str, category: str,
                             department: str | None, academic_year: str | None,
                             chunks: list[dict]) -> int:
        """
        chunks: list of {"chunk_index": int, "page_number": int|None, "text": str}
        Returns number of vectors upserted.
        """
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        vectors = embed_texts(texts)

        upserts = []
        for chunk, vector in zip(chunks, vectors):
            vector_id = f"doc-{document_id}-chunk-{chunk['chunk_index']}"
            metadata = {
                "document_id": document_id,
                "document_title": document_title,
                "category": category,
                "department": department or "",
                "academic_year": academic_year or "",
                "page_number": chunk["page_number"] or 0,
                "chunk_index": chunk["chunk_index"],
                "source_type": "pdf",
                # Storing chunk text in metadata simplifies retrieval (no second DB
                # round-trip needed) and keeps individual vector payloads small
                # since chunks are capped at CHUNK_SIZE characters.
                "text": chunk["text"],
            }
            upserts.append({"id": vector_id, "values": vector, "metadata": metadata})

        # Batch upserts to avoid oversized requests
        batch_size = 100
        for i in range(0, len(upserts), batch_size):
            self._index.upsert(vectors=upserts[i:i + batch_size], namespace=self._namespace)

        return len(upserts)

    def delete_document_vectors(self, document_id: int) -> None:
        try:
            self._index.delete(filter={"document_id": document_id}, namespace=self._namespace)
        except Exception as exc:
            # Surface failures rather than silently pretending success -
            # caller (document_service) decides how to report this to the admin.
            raise RuntimeError(f"Failed to delete vectors for document {document_id}: {exc}") from exc

    def similarity_search(self, query: str, top_k: int, category: str | None = None, fetch_k: int | None = None) -> list[dict]:
        query_vector = embed_text(query)
        filter_dict = {"category": category} if category else None

        result = self._index.query(
            vector=query_vector,
            top_k=fetch_k or top_k,
            namespace=self._namespace,
            include_metadata=True,
            filter=filter_dict,
        )

        matches = []
        for match in result.get("matches", []):
            metadata = match.get("metadata", {})
            matches.append({
                "score": match.get("score", 0.0),
                "document_id": metadata.get("document_id"),
                "document_title": metadata.get("document_title"),
                "page_number": metadata.get("page_number"),
                "chunk_index": metadata.get("chunk_index"),
                "text": metadata.get("text", ""),
            })
        return matches


@lru_cache
def get_vector_service() -> VectorStoreService:
    return VectorStoreService()

"""
Retriever: turns a raw student question into the final set of context
chunks handed to the LLM. Four responsibilities, in order:

1. Query rewriting - a short follow-up ("lowest one?") has almost no
   semantic content on its own, so it's rewritten into a standalone
   question using recent conversation history before embedding.
2. Dense (semantic) search - the existing Pinecone vector search.
3. Hybrid re-ranking - dense search alone can miss exact terms (a CGPA
   number, a specific circular code). We fetch a larger candidate pool
   and boost candidates that also share keywords with the question, then
   re-sort by the combined score. This is retrieve-then-rerank hybrid
   search, not true sparse+dense fusion, but needs no extra
   infrastructure (no BM25 index, no new dependency) while still meaningfully
   improving exact-term recall.
4. Cross-document diversity - for comparison-style questions ("compare X
   and Y", "difference between..."), dense search alone tends to return
   many near-duplicate chunks from a single document. We cap how many
   chunks any one document can contribute so multiple sources have a
   chance to appear together in the context.

The relevance threshold (RAG_MIN_SCORE) is applied last, against the
original dense similarity score - re-ranking only changes ORDER, never
what counts as "relevant enough to trust".
"""
import logging
import re

from app.core.config import settings
from app.services.vector_service import VectorStoreService

logger = logging.getLogger("campus_assistant.rag")

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "for", "to",
    "and", "or", "what", "when", "where", "which", "who", "how", "does", "do",
    "did", "i", "me", "my", "please", "tell", "about", "with", "this", "that",
}

_COMPARISON_PATTERN = re.compile(r"\b(compare|comparison|versus|vs\.?|difference between|both)\b", re.IGNORECASE)

QUERY_REWRITE_PROMPT = """Rewrite the question below into the best possible search query for finding it in
official college documents. Two things to fix, if needed:

1. Resolve context from the conversation (e.g. "it", "that", "the lowest one" into what they refer to).
2. Expand common abbreviations into their full form, since documents usually spell things out
   (e.g. "VC" -> "Vice Chancellor", "JMI" -> "Jamia Millia Islamia", "CGPA" -> "CGPA cumulative grade point average").

Rules:
- Output ONLY the rewritten question, nothing else - no preamble, no quotes.
- If the question is already clear and standalone, output it unchanged.
- Never answer the question - only rewrite it for search purposes.

Conversation history:
{history}

Question: {question}

Search query:"""


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def rewrite_query(llm, question: str, history: list[dict]) -> str:
    """
    Uses the LLM to turn the question into a better search query - both for
    context-dependent follow-ups ("lowest one?") AND for the very first
    message in a conversation, where common abbreviations ("VC", "JMI")
    often don't match the source documents' actual wording closely enough
    for dense embedding search to find them. This only affects what gets
    embedded for search; the original question (unmodified) is still what
    the LLM answers from - see rag_service.py.

    Falls back to the raw question (never blocks the request) if the
    rewrite call fails for any reason - this is a search-quality
    improvement, not a critical-path dependency.
    """
    recent = history[-(settings.CHAT_HISTORY_TURNS * 2):]
    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in recent) if recent else "(no previous messages)"

    try:
        response = llm.invoke(QUERY_REWRITE_PROMPT.format(history=history_text, question=question))
        rewritten = response.content.strip().strip('"')
        return rewritten if rewritten else question
    except Exception:
        logger.warning("Query rewrite failed, falling back to raw question", exc_info=True)
        return question


def _hybrid_rerank(matches: list[dict], question: str) -> list[dict]:
    """Boost candidates that share keywords with the question, then re-sort.
    Combined score is only used for ORDERING candidates before the top_k cut -
    the original dense `score` is preserved untouched for the relevance
    threshold check in rag_service."""
    q_words = _keywords(question)
    if not q_words:
        return matches

    def combined(m: dict) -> float:
        overlap = len(q_words & _keywords(m.get("text", "")))
        keyword_boost = min(overlap / max(len(q_words), 1), 1.0) * 0.15
        return m["score"] + keyword_boost

    return sorted(matches, key=combined, reverse=True)


def _diversify_by_document(matches: list[dict], top_k: int, max_per_document: int = 2) -> list[dict]:
    """Cap chunks per document so cross-document questions (comparisons)
    can surface more than one source, instead of one document dominating
    every slot in the context window."""
    per_doc_count: dict = {}
    diversified = []
    leftovers = []

    for m in matches:
        doc_id = m.get("document_id")
        if per_doc_count.get(doc_id, 0) < max_per_document:
            diversified.append(m)
            per_doc_count[doc_id] = per_doc_count.get(doc_id, 0) + 1
        else:
            leftovers.append(m)

    diversified.extend(leftovers)
    return diversified[:top_k]


def retrieve_relevant_chunks(
    vector_service: VectorStoreService,
    question: str,
    history: list[dict] | None = None,
    llm=None,
) -> list[dict]:
    history = history or []
    search_query = rewrite_query(llm, question, history) if llm is not None else question

    is_comparison = bool(_COMPARISON_PATTERN.search(question))
    top_k = settings.RAG_TOP_K
    # Fetch a larger candidate pool so hybrid re-ranking and diversity have
    # something to work with beyond just the top_k dense matches.
    fetch_k = max(top_k * 4, 20)

    raw_matches = vector_service.similarity_search(search_query, top_k=top_k, fetch_k=fetch_k)

    reranked = _hybrid_rerank(raw_matches, search_query)

    max_per_document = 2 if is_comparison else 3
    diversified = _diversify_by_document(reranked, top_k, max_per_document=max_per_document)

    # NOTE: RAG_MIN_SCORE=0.70 is a starting point, not a universal constant -
    # it should be tuned against real college documents and real student
    # questions during testing. Cosine similarity behaves differently across
    # embedding models, so re-tune this if EMBEDDING_MODEL changes. Filtering
    # happens on the ORIGINAL dense score, not the reranked/boosted one.
    relevant = [m for m in diversified if m["score"] >= settings.RAG_MIN_SCORE]
    return relevant






# """
# Retriever: wraps VectorStoreService.similarity_search with the configurable
# relevance threshold (RAG_MIN_SCORE). This is the safeguard that stops the
# chatbot from confidently answering off irrelevant chunks.
# """
# from app.core.config import settings
# from app.services.vector_service import VectorStoreService


# def build_search_query(question: str, history: list[dict]) -> str:
#     """
#     Short follow-up questions ("lowest one?", "what about hostel?") have
#     almost no semantic content on their own, so embedding them alone often
#     fails to match anything relevant. Prepending the last user turn(s) gives
#     the embedding enough context to find the right chunks, while the LLM
#     prompt itself still receives the question exactly as the student typed it.
#     """
#     if not history:
#         return question

#     recent_user_turns = [h["content"] for h in history if h["role"] == "USER"][-2:]
#     if not recent_user_turns:
#         return question

#     return " ".join(recent_user_turns + [question])


# def retrieve_relevant_chunks(vector_service: VectorStoreService, question: str, history: list[dict] | None = None) -> list[dict]:
#     search_query = build_search_query(question, history or [])
#     raw_matches = vector_service.similarity_search(search_query, top_k=settings.RAG_TOP_K)

#     # NOTE: RAG_MIN_SCORE=0.70 is a starting point, not a universal constant -
#     # it should be tuned against real college documents and real student
#     # questions during testing. Cosine similarity behaves differently across
#     # embedding models, so re-tune this if EMBEDDING_MODEL changes.
#     relevant = [m for m in raw_matches if m["score"] >= settings.RAG_MIN_SCORE]
#     return relevant

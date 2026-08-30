"""
RAGService: the orchestration layer for question -> answer + sources.

Flow: validate question -> rewrite query -> retrieve relevant chunks (with
threshold, hybrid rerank, diversity) -> build prompt -> call LLM -> return
answer text + source list. answer_question() returns the full answer at
once; stream_answer() yields it token-by-token for the streaming endpoint.

This module never touches the DB directly - chat_service is responsible
for persisting messages/sources. That keeps rag_service testable in
isolation with a mocked vector store + mocked LLM.
"""
import logging
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.rag.prompts import (
    NO_CONTEXT_FOUND_MESSAGE,
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
    build_context_block,
    build_history_block,
)
from app.rag.retriever import retrieve_relevant_chunks
from app.services.vector_service import VectorStoreService, get_vector_service

logger = logging.getLogger("campus_assistant.rag")


class RAGService:
    def __init__(self, vector_service: VectorStoreService):
        self.vector_service = vector_service
        self._llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,  # low temperature: prioritize faithfulness over creativity
        )

    def _retrieve(self, question: str, history: list[dict]) -> list[dict] | None:
        """Returns None on retrieval failure, [] if nothing relevant found,
        otherwise the list of relevant chunks. Shared by answer_question()
        and stream_answer() so both go through identical retrieval logic."""
        try:
            return retrieve_relevant_chunks(self.vector_service, question, history, llm=self._llm)
        except Exception:
            logger.exception("RAG retrieval failed for question: %r", question)
            return None

    def answer_question(self, question: str, history: list[dict]) -> dict:
        """
        Returns:
        {
          "answer": str,
          "sources": [{"document_id", "document_title", "page_number", "similarity_score"}],
          "debug": {"retrieved_chunks": [...]}   # for admin/debug visibility only
        }
        """
        question = question.strip()
        if not question:
            return {"answer": NO_CONTEXT_FOUND_MESSAGE, "sources": [], "debug": {"retrieved_chunks": []}}

        relevant_chunks = self._retrieve(question, history)
        if relevant_chunks is None:
            return {
                "answer": "Something went wrong while searching college documents. Please try again shortly.",
                "sources": [],
                "debug": {"retrieved_chunks": []},
            }

        if not relevant_chunks:
            logger.info("No sufficiently relevant chunks found for question: %r", question)
            return {"answer": NO_CONTEXT_FOUND_MESSAGE, "sources": [], "debug": {"retrieved_chunks": []}}

        context_block = build_context_block(relevant_chunks)
        history_block = build_history_block(history[-(settings.CHAT_HISTORY_TURNS * 2):])
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
            context=context_block, history=history_block, question=question
        )

        try:
            response = self._llm.invoke(
                [
                    ("system", RAG_SYSTEM_PROMPT),
                    ("human", user_prompt),
                ]
            )
            answer_text = response.content
        except Exception:
            logger.exception("LLM call failed for question: %r", question)
            return {
                "answer": "The assistant is temporarily unavailable. Please try again shortly.",
                "sources": [],
                "debug": {"retrieved_chunks": relevant_chunks},
            }

        sources = self._format_sources(relevant_chunks)
        return {"answer": answer_text, "sources": sources, "debug": {"retrieved_chunks": relevant_chunks}}

    def stream_answer(self, question: str, history: list[dict]):
        """
        Generator yielding dicts as the answer is produced:
          {"type": "sources", "sources": [...]}   - sent once, before tokens
          {"type": "token", "text": "..."}         - one per streamed chunk
          {"type": "done", "answer": "<full text>"} - final event with full answer
        Callers (the streaming route) persist the final answer once "done" arrives.
        """
        question = question.strip()
        if not question:
            yield {"type": "sources", "sources": []}
            yield {"type": "token", "text": NO_CONTEXT_FOUND_MESSAGE}
            yield {"type": "done", "answer": NO_CONTEXT_FOUND_MESSAGE}
            return

        relevant_chunks = self._retrieve(question, history)

        if relevant_chunks is None:
            msg = "Something went wrong while searching college documents. Please try again shortly."
            yield {"type": "sources", "sources": []}
            yield {"type": "token", "text": msg}
            yield {"type": "done", "answer": msg}
            return

        if not relevant_chunks:
            logger.info("No sufficiently relevant chunks found for question: %r", question)
            yield {"type": "sources", "sources": []}
            yield {"type": "token", "text": NO_CONTEXT_FOUND_MESSAGE}
            yield {"type": "done", "answer": NO_CONTEXT_FOUND_MESSAGE}
            return

        sources = self._format_sources(relevant_chunks)
        yield {"type": "sources", "sources": sources}

        context_block = build_context_block(relevant_chunks)
        history_block = build_history_block(history[-(settings.CHAT_HISTORY_TURNS * 2):])
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
            context=context_block, history=history_block, question=question
        )

        full_answer = ""
        try:
            for chunk in self._llm.stream(
                [
                    ("system", RAG_SYSTEM_PROMPT),
                    ("human", user_prompt),
                ]
            ):
                piece = chunk.content or ""
                if piece:
                    full_answer += piece
                    yield {"type": "token", "text": piece}
        except Exception:
            logger.exception("Streaming LLM call failed for question: %r", question)
            if not full_answer:
                full_answer = "The assistant is temporarily unavailable. Please try again shortly."
                yield {"type": "token", "text": full_answer}

        yield {"type": "done", "answer": full_answer}

    @staticmethod
    def _format_sources(relevant_chunks: list[dict]) -> list[dict]:
        return [
            {
                "document_id": c["document_id"],
                "document_title": c["document_title"],
                "page_number": c["page_number"],
                "similarity_score": round(float(c["score"]), 4),
            }
            for c in relevant_chunks
        ]


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(get_vector_service())





# """
# RAGService: the orchestration layer for question -> answer + sources.

# Flow: validate question -> retrieve relevant chunks (with threshold) ->
# build prompt -> call LLM -> return answer text + source list.

# This module never touches the DB directly - chat_service is responsible
# for persisting messages/sources. That keeps rag_service testable in
# isolation with a mocked vector store + mocked LLM.
# """
# import logging
# from functools import lru_cache

# from langchain_google_genai import ChatGoogleGenerativeAI

# from app.core.config import settings
# from app.rag.prompts import (
#     NO_CONTEXT_FOUND_MESSAGE,
#     RAG_SYSTEM_PROMPT,
#     RAG_USER_PROMPT_TEMPLATE,
#     build_context_block,
#     build_history_block,
# )
# from app.rag.retriever import retrieve_relevant_chunks
# from app.services.vector_service import VectorStoreService, get_vector_service

# logger = logging.getLogger("campus_assistant.rag")


# class RAGService:
#     def __init__(self, vector_service: VectorStoreService):
#         self.vector_service = vector_service
#         self._llm = ChatGoogleGenerativeAI(
#             model=settings.LLM_MODEL,
#             google_api_key=settings.GEMINI_API_KEY,
#             temperature=0.1,  # low temperature: prioritize faithfulness over creativity
#         )

#     def answer_question(self, question: str, history: list[dict]) -> dict:
#         """
#         Returns:
#         {
#           "answer": str,
#           "sources": [{"document_id", "document_title", "page_number", "similarity_score"}],
#           "debug": {"retrieved_chunks": [...]}   # for admin/debug visibility only
#         }
#         """
#         question = question.strip()
#         if not question:
#             return {"answer": NO_CONTEXT_FOUND_MESSAGE, "sources": [], "debug": {"retrieved_chunks": []}}

#         try:
#             relevant_chunks = retrieve_relevant_chunks(self.vector_service, question, history)
#         except Exception:
#             logger.exception("RAG retrieval failed for question: %r", question)
#             return {
#                 "answer": "Something went wrong while searching college documents. Please try again shortly.",
#                 "sources": [],
#                 "debug": {"retrieved_chunks": []},
#             }

#         if not relevant_chunks:
#             logger.info("No sufficiently relevant chunks found for question: %r", question)
#             return {"answer": NO_CONTEXT_FOUND_MESSAGE, "sources": [], "debug": {"retrieved_chunks": []}}

#         context_block = build_context_block(relevant_chunks)
#         history_block = build_history_block(history[-(settings.CHAT_HISTORY_TURNS * 2):])
#         user_prompt = RAG_USER_PROMPT_TEMPLATE.format(
#             context=context_block, history=history_block, question=question
#         )

#         try:
#             response = self._llm.invoke(
#                 [
#                     ("system", RAG_SYSTEM_PROMPT),
#                     ("human", user_prompt),
#                 ]
#             )
#             answer_text = response.content
#         except Exception:
#             logger.exception("LLM call failed for question: %r", question)
#             return {
#                 "answer": "The assistant is temporarily unavailable. Please try again shortly.",
#                 "sources": [],
#                 "debug": {"retrieved_chunks": relevant_chunks},
#             }

#         sources = [
#             {
#                 "document_id": c["document_id"],
#                 "document_title": c["document_title"],
#                 "page_number": c["page_number"],
#                 "similarity_score": round(float(c["score"]), 4),
#             }
#             for c in relevant_chunks
#         ]

#         return {"answer": answer_text, "sources": sources, "debug": {"retrieved_chunks": relevant_chunks}}


# @lru_cache
# def get_rag_service() -> RAGService:
#     return RAGService(get_vector_service())

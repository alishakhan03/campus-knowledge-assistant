import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message, MessageFeedback, MessageRole, MessageSource
from app.services.rag_service import get_rag_service

logger = logging.getLogger("campus_assistant.chat")


def get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def build_history(conversation: Conversation) -> list[dict]:
    return [{"role": m.role.value, "content": m.content} for m in conversation.messages]


def ask_question(db: Session, conversation: Conversation, question: str) -> tuple[Message, list[dict]]:
    history = build_history(conversation)

    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=question)
    db.add(user_message)
    db.flush()

    try:
        rag_service = get_rag_service()
        result = rag_service.answer_question(question, history)
    except Exception:
        logger.exception("RAG service unavailable while answering question")
        result = {
            "answer": (
                "The assistant is temporarily unavailable (couldn't reach the document "
                "search service). Please try again in a moment."
            ),
            "sources": [],
        }

    assistant_message = _persist_assistant_message(db, conversation, result["answer"], result["sources"])
    return assistant_message, result["sources"]


def _persist_assistant_message(
    db: Session, conversation: Conversation, answer: str, sources: list[dict]
) -> Message:
    assistant_message = Message(conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=answer)
    db.add(assistant_message)
    db.flush()

    for source in sources:
        db.add(
            MessageSource(
                message_id=assistant_message.id,
                document_id=source["document_id"],
                page_number=source["page_number"],
                similarity_score=source["similarity_score"],
            )
        )

    db.commit()
    db.refresh(assistant_message)
    return assistant_message


def start_question(db: Session, conversation: Conversation, question: str) -> tuple[Message, list[dict]]:
    """Used by the streaming endpoint: persists the user's message and
    returns (history-before-this-question, ...) so the route can stream the
    answer, then call finish_streamed_answer() once generation completes."""
    history = build_history(conversation)
    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=question)
    db.add(user_message)
    db.commit()
    return user_message, history


def finish_streamed_answer(
    db: Session, conversation_id: int, answer: str, sources: list[dict], first_question: str
) -> Message:
    conversation = db.get(Conversation, conversation_id)
    assistant_message = _persist_assistant_message(db, conversation, answer, sources)

    if conversation.title == "New Conversation":
        conversation.title = first_question[:80]
        db.commit()

    return assistant_message


def set_message_feedback(db: Session, user_id: int, message_id: int, is_helpful: bool) -> MessageFeedback:
    """Records (or updates) a thumbs-up/thumbs-down rating on an assistant
    message. Ownership is checked through the message's conversation so a
    student can only rate messages from their own conversations."""
    message = db.get(Message, message_id)
    if message is None or message.role != MessageRole.ASSISTANT:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")

    conversation = db.get(Conversation, message.conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")

    existing = db.query(MessageFeedback).filter(MessageFeedback.message_id == message_id).first()
    if existing:
        existing.is_helpful = is_helpful
        db.commit()
        db.refresh(existing)
        return existing

    feedback = MessageFeedback(message_id=message_id, is_helpful=is_helpful)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback









# import logging

# from fastapi import HTTPException, status
# from sqlalchemy.orm import Session

# from app.models.conversation import Conversation
# from app.models.message import Message, MessageRole, MessageSource
# from app.services.rag_service import get_rag_service

# logger = logging.getLogger("campus_assistant.chat")


# def get_owned_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation:
#     conversation = db.get(Conversation, conversation_id)
#     if conversation is None or conversation.user_id != user_id:
#         # Same error for "not found" and "not yours" - avoids leaking existence
#         # of other users' conversation IDs.
#         raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")
#     return conversation


# def build_history(conversation: Conversation) -> list[dict]:
#     return [{"role": m.role.value, "content": m.content} for m in conversation.messages]


# def ask_question(db: Session, conversation: Conversation, question: str) -> tuple[Message, list[dict]]:
#     history = build_history(conversation)

#     user_message = Message(conversation_id=conversation.id, role=MessageRole.USER, content=question)
#     db.add(user_message)
#     db.flush()  # get an id without committing yet

#     try:
#         rag_service = get_rag_service()
#         result = rag_service.answer_question(question, history)
#     except Exception:
#         # If the vector store or LLM client fails to even initialize (bad
#         # API key, unreachable network, misconfigured index, etc.) this
#         # degrades to a clear in-chat message instead of a raw 500.
#         logger.exception("RAG service unavailable while answering question")
#         result = {
#             "answer": (
#                 "The assistant is temporarily unavailable (couldn't reach the document "
#                 "search service). Please try again in a moment."
#             ),
#             "sources": [],
#         }

#     assistant_message = Message(
#         conversation_id=conversation.id, role=MessageRole.ASSISTANT, content=result["answer"]
#     )
#     db.add(assistant_message)
#     db.flush()

#     for source in result["sources"]:
#         db.add(
#             MessageSource(
#                 message_id=assistant_message.id,
#                 document_id=source["document_id"],
#                 page_number=source["page_number"],
#                 similarity_score=source["similarity_score"],
#             )
#         )

#     # Auto-title new conversations from the first question
#     if conversation.title == "New Conversation":
#         conversation.title = question[:80]

#     db.commit()
#     db.refresh(assistant_message)
#     return assistant_message, result["sources"]

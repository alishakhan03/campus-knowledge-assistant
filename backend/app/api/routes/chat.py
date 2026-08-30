import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import SessionLocal, get_db
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import (
    ChatAnswerResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationPublic,
    FeedbackPublic,
    FeedbackRequest,
    MessageCreate,
    MessagePublic,
    SourcePublic,
)
from app.services.chat_service import (
    ask_question,
    finish_streamed_answer,
    get_owned_conversation,
    set_message_feedback,
    start_question,
)
from app.services.rag_service import get_rag_service

logger = logging.getLogger("campus_assistant.chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationPublic, status_code=201, summary="Start a new conversation")
def create_conversation(
    payload: ConversationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    conversation = Conversation(user_id=current_user.id, title=payload.title or "New Conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationPublic], summary="List my conversations")
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail, summary="Get one conversation with messages")
def get_conversation(
    conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    conversation = get_owned_conversation(db, conversation_id, current_user.id)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204, summary="Delete my conversation")
def delete_conversation(
    conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    conversation = get_owned_conversation(db, conversation_id, current_user.id)
    db.delete(conversation)
    db.commit()


def _enrich_sources(db: Session, raw_sources: list[dict]) -> list[dict]:
    doc_ids = {s["document_id"] for s in raw_sources}
    docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()} if doc_ids else {}
    return [
        {
            "document_id": s["document_id"],
            "document_title": docs[s["document_id"]].title if s["document_id"] in docs else "Unknown document",
            "page_number": s["page_number"],
            "similarity_score": s["similarity_score"],
        }
        for s in raw_sources
    ]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatAnswerResponse,
    summary="Ask a question in a conversation (full response, not streamed)",
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = get_owned_conversation(db, conversation_id, current_user.id)
    assistant_message, sources = ask_question(db, conversation, payload.content)

    enriched_sources = [SourcePublic(**s) for s in _enrich_sources(db, sources)]
    return ChatAnswerResponse(message=MessagePublic.model_validate(assistant_message), sources=enriched_sources)


@router.post(
    "/conversations/{conversation_id}/messages/stream",
    summary="Ask a question with a token-by-token streamed response (Server-Sent Events)",
)
def send_message_stream(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streams Server-Sent Events, each a JSON line prefixed with "data: ":
      {"type": "sources", "sources": [...]}   - sent once, right away
      {"type": "token", "text": "..."}         - one per generated chunk
      {"type": "done", "message_id": <id>}     - final event once persisted
      {"type": "error", "text": "..."}         - only on unexpected failure

    The request-scoped `db` session is used only to validate ownership and
    persist the user's message before streaming starts. The generator below
    opens its OWN session (stream_db) because it keeps running after this
    endpoint function returns and FastAPI closes the `db` dependency -
    StreamingResponse hands control back to Starlette immediately, then the
    generator is drained afterward.
    """
    conversation = get_owned_conversation(db, conversation_id, current_user.id)
    _user_message, history = start_question(db, conversation, payload.content)
    first_question = payload.content

    def event_stream():
        stream_db = SessionLocal()
        raw_sources: list[dict] = []
        try:
            rag_service = get_rag_service()
            for event in rag_service.stream_answer(payload.content, history):
                if event["type"] == "sources":
                    raw_sources = event["sources"]
                    enriched = _enrich_sources(stream_db, raw_sources)
                    yield f"data: {json.dumps({'type': 'sources', 'sources': enriched})}\n\n"
                elif event["type"] == "token":
                    yield f"data: {json.dumps({'type': 'token', 'text': event['text']})}\n\n"
                elif event["type"] == "done":
                    assistant_message = finish_streamed_answer(
                        stream_db, conversation_id, event["answer"], raw_sources, first_question
                    )
                    yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"
        except Exception:
            logger.exception("Streaming chat response failed")
            yield f"data: {json.dumps({'type': 'error', 'text': 'Something went wrong. Please try again.'})}\n\n"
        finally:
            stream_db.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/messages/{message_id}/feedback",
    response_model=FeedbackPublic,
    summary="Rate an assistant message as helpful or not (thumbs up/down)",
)
def rate_message(
    message_id: int,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feedback = set_message_feedback(db, current_user.id, message_id, payload.is_helpful)
    return FeedbackPublic(message_id=feedback.message_id, is_helpful=feedback.is_helpful)








# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session

# from app.core.dependencies import get_current_user
# from app.db.database import get_db
# from app.models.conversation import Conversation
# from app.models.document import Document
# from app.models.user import User
# from app.schemas.chat import (
#     ChatAnswerResponse,
#     ConversationCreate,
#     ConversationDetail,
#     ConversationPublic,
#     MessageCreate,
#     MessagePublic,
#     SourcePublic,
# )
# from app.services.chat_service import ask_question, get_owned_conversation

# router = APIRouter(prefix="/api/chat", tags=["chat"])


# @router.post("/conversations", response_model=ConversationPublic, status_code=201, summary="Start a new conversation")
# def create_conversation(
#     payload: ConversationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
# ):
#     conversation = Conversation(user_id=current_user.id, title=payload.title or "New Conversation")
#     db.add(conversation)
#     db.commit()
#     db.refresh(conversation)
#     return conversation


# @router.get("/conversations", response_model=list[ConversationPublic], summary="List my conversations")
# def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return (
#         db.query(Conversation)
#         .filter(Conversation.user_id == current_user.id)
#         .order_by(Conversation.updated_at.desc())
#         .all()
#     )


# @router.get("/conversations/{conversation_id}", response_model=ConversationDetail, summary="Get one conversation with messages")
# def get_conversation(
#     conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
# ):
#     conversation = get_owned_conversation(db, conversation_id, current_user.id)
#     return conversation


# @router.delete("/conversations/{conversation_id}", status_code=204, summary="Delete my conversation")
# def delete_conversation(
#     conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
# ):
#     conversation = get_owned_conversation(db, conversation_id, current_user.id)
#     db.delete(conversation)
#     db.commit()


# @router.post(
#     "/conversations/{conversation_id}/messages",
#     response_model=ChatAnswerResponse,
#     summary="Ask a question in a conversation",
# )
# def send_message(
#     conversation_id: int,
#     payload: MessageCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     conversation = get_owned_conversation(db, conversation_id, current_user.id)
#     assistant_message, sources = ask_question(db, conversation, payload.content)

#     # Enrich sources with document titles for the response
#     enriched_sources = []
#     for s in sources:
#         doc = db.get(Document, s["document_id"])
#         enriched_sources.append(
#             SourcePublic(
#                 document_id=s["document_id"],
#                 document_title=doc.title if doc else "Unknown document",
#                 page_number=s["page_number"],
#                 similarity_score=s["similarity_score"],
#             )
#         )

#     return ChatAnswerResponse(message=MessagePublic.model_validate(assistant_message), sources=enriched_sources)

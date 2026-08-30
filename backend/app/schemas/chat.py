from datetime import datetime

from pydantic import BaseModel, Field

from app.models.message import MessageRole


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationPublic(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SourcePublic(BaseModel):
    document_id: int
    document_title: str
    page_number: int | None
    similarity_score: float | None

    class Config:
        from_attributes = True


class MessagePublic(BaseModel):
    id: int
    role: MessageRole
    content: str
    created_at: datetime
    is_helpful: bool | None = None

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    is_helpful: bool


class FeedbackPublic(BaseModel):
    message_id: int
    is_helpful: bool

    class Config:
        from_attributes = True


class ConversationDetail(ConversationPublic):
    messages: list[MessagePublic] = []


class ChatAnswerResponse(BaseModel):
    message: MessagePublic
    sources: list[SourcePublic]

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.document import DocumentCategory, DocumentStatus


class DocumentCreateForm(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: DocumentCategory
    department: str | None = None
    academic_year: str | None = None


class DocumentPublic(BaseModel):
    id: int
    title: str
    description: str | None
    category: DocumentCategory
    department: str | None
    academic_year: str | None
    status: DocumentStatus
    processing_error: str | None
    page_count: int | None
    chunk_count: int | None
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentStats(BaseModel):
    total: int
    processed: int
    processing: int
    failed: int
    uploaded: int

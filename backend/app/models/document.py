import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class DocumentCategory(str, enum.Enum):
    ACADEMIC = "ACADEMIC"
    EXAMINATION = "EXAMINATION"
    ADMISSION = "ADMISSION"
    SCHOLARSHIP = "SCHOLARSHIP"
    HOSTEL = "HOSTEL"
    PLACEMENT = "PLACEMENT"
    DEPARTMENT = "DEPARTMENT"
    GENERAL = "GENERAL"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)  # safe, server-generated name
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[DocumentCategory] = mapped_column(Enum(DocumentCategory), index=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.UPLOADED, index=True, nullable=False
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    uploader = relationship("User", back_populates="documents_uploaded")
    sources = relationship("MessageSource", back_populates="document")

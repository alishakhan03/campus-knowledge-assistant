import logging
import os

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.rag.ingestion import PdfExtractionError, process_pdf
from app.schemas.document import DocumentCreateForm
from app.services.vector_service import VectorStoreService, get_vector_service
from app.utils.file_utils import safe_filename, save_upload, validate_pdf_upload

logger = logging.getLogger("campus_assistant.documents")


def create_document_record(db: Session, form: DocumentCreateForm, file: UploadFile,
                            content: bytes, uploader_id: int) -> Document:
    validate_pdf_upload(file, content)

    filename = safe_filename(file.filename or "upload.pdf")
    file_path = save_upload(content, filename)

    document = Document(
        title=form.title,
        file_name=filename,
        original_file_name=file.filename or "upload.pdf",
        description=form.description,
        category=form.category,
        department=form.department,
        academic_year=form.academic_year,
        file_path=file_path,
        status=DocumentStatus.UPLOADED,
        uploaded_by=uploader_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def process_document(document_id: int, db_session_factory) -> None:
    """
    Runs as a FastAPI BackgroundTask. Takes a session factory (not a session)
    because the request-scoped session will already be closed by the time
    this background task actually runs.
    """
    db: Session = db_session_factory()
    try:
        document = db.get(Document, document_id)
        if document is None:
            logger.error("process_document: document %s not found", document_id)
            return

        document.status = DocumentStatus.PROCESSING
        db.commit()
        logger.info("Started processing document %s (%s)", document.id, document.title)

        try:
            pages, chunks = process_pdf(document.file_path)
        except PdfExtractionError as exc:
            document.status = DocumentStatus.FAILED
            document.processing_error = str(exc)
            db.commit()
            logger.warning("Document %s failed extraction: %s", document.id, exc)
            return
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.processing_error = "Unexpected error during text extraction."
            db.commit()
            logger.exception("Document %s failed extraction unexpectedly", document.id)
            return

        try:
            vector_service: VectorStoreService = get_vector_service()
            chunk_dicts = [
                {"chunk_index": c.chunk_index, "page_number": c.page_number, "text": c.text} for c in chunks
            ]
            vector_count = vector_service.add_document_chunks(
                document_id=document.id,
                document_title=document.title,
                category=document.category.value,
                department=document.department,
                academic_year=document.academic_year,
                chunks=chunk_dicts,
            )
        except Exception:
            document.status = DocumentStatus.FAILED
            document.processing_error = "Failed to generate/store embeddings. See server logs."
            db.commit()
            logger.exception("Document %s failed at embedding/storage stage", document.id)
            return

        document.status = DocumentStatus.PROCESSED
        document.page_count = len(pages)
        document.chunk_count = vector_count
        document.processing_error = None
        db.commit()
        logger.info("Finished processing document %s: %s pages, %s chunks", document.id, len(pages), vector_count)
    finally:
        db.close()


def delete_document(db: Session, document: Document) -> None:
    vector_service = get_vector_service()
    try:
        vector_service.delete_document_vectors(document.id)
    except RuntimeError:
        # Do not silently pretend success - block deletion of DB record so we
        # don't end up with orphaned vectors that no longer map to anything.
        logger.exception("Vector deletion failed for document %s; aborting delete", document.id)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove document vectors. Document was not deleted.",
        )

    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except OSError:
            logger.warning("Could not remove file %s from disk", document.file_path)

    db.delete(document)
    db.commit()

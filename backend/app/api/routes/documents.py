from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.dependencies import get_current_user, require_admin
from app.db.database import SessionLocal, get_db
from app.models.document import Document, DocumentCategory, DocumentStatus
from app.models.user import User
from app.schemas.document import DocumentCreateForm, DocumentPublic, DocumentStats
from app.services.document_service import create_document_record, delete_document, process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentPublic, status_code=201, summary="Upload a college PDF (admin only)")
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str | None = Form(None),
    category: DocumentCategory = Form(...),
    department: str | None = Form(None),
    academic_year: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    content = await file.read()
    form = DocumentCreateForm(
        title=title, description=description, category=category,
        department=department, academic_year=academic_year,
    )
    document = create_document_record(db, form, file, content, admin.id)

    # BackgroundTasks runs after the response is sent; it gets its own DB
    # session via SessionLocal since the request-scoped session will close.
    background_tasks.add_task(process_document, document.id, SessionLocal)
    return document


@router.get("", response_model=list[DocumentPublic], summary="List all documents (admin only)")
def list_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/stats", response_model=DocumentStats, summary="Document processing statistics (admin only)")
def document_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    docs = db.query(Document).all()
    return DocumentStats(
        total=len(docs),
        processed=sum(1 for d in docs if d.status == DocumentStatus.PROCESSED),
        processing=sum(1 for d in docs if d.status == DocumentStatus.PROCESSING),
        failed=sum(1 for d in docs if d.status == DocumentStatus.FAILED),
        uploaded=sum(1 for d in docs if d.status == DocumentStatus.UPLOADED),
    )


@router.get("/{document_id}", response_model=DocumentPublic, summary="Get a single document (any logged-in user)")
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document

@router.get("/{document_id}/file", summary="Download/preview the original PDF (any logged-in user)")
def get_document_file(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="The original file is no longer available on disk")
    return FileResponse(
        document.file_path,
        media_type="application/pdf",
        filename=document.original_file_name,
    )
    
@router.delete("/{document_id}", status_code=204, summary="Delete a document and its vectors (admin only)")
def remove_document(document_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    delete_document(db, document)


@router.post("/{document_id}/reprocess", response_model=DocumentPublic, summary="Reprocess a document (admin only)")
def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Clear old vectors first so reprocessing never leaves duplicates behind.
    from app.services.vector_service import get_vector_service
    try:
        get_vector_service().delete_document_vectors(document.id)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    document.status = DocumentStatus.UPLOADED
    document.processing_error = None
    document.chunk_count = None
    db.commit()

    background_tasks.add_task(process_document, document.id, SessionLocal)
    return document

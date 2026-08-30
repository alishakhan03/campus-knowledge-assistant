"""
Document ingestion pipeline: PDF -> per-page text -> cleaned text -> chunks.

Kept independent of Pinecone/DB so it can be unit-tested with plain PDF bytes.
"""
import re
from dataclasses import dataclass

import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


class PdfExtractionError(Exception):
    """Raised when a PDF has no extractable text at all."""


@dataclass
class ExtractedPage:
    page_number: int  # 1-indexed, human-friendly
    text: str


@dataclass
class Chunk:
    chunk_index: int
    page_number: int | None
    text: str


def extract_pages_from_pdf(file_path: str) -> list[ExtractedPage]:
    """Extract text per page, preserving page numbers for citation purposes."""
    pages: list[ExtractedPage] = []
    with fitz.open(file_path) as doc:
        for i, page in enumerate(doc, start=1):
            raw_text = page.get_text("text")
            if raw_text and raw_text.strip():
                pages.append(ExtractedPage(page_number=i, text=raw_text))

    if not pages:
        raise PdfExtractionError(
            "No extractable text was found in this PDF. It may be a scanned "
            "image-only document, which is not supported (OCR is out of scope)."
        )
    return pages


def clean_text(text: str) -> str:
    """
    Conservative cleaning: collapse excessive whitespace/blank lines and strip
    obvious extraction artifacts, without altering numbers, dates, or wording.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ blank lines into a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse repeated spaces/tabs (but not newlines)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def chunk_pages(pages: list[ExtractedPage]) -> list[Chunk]:
    """
    Chunk cleaned page text using a recursive character splitter, tracking
    which page each chunk primarily came from.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    chunk_index = 0
    for page in pages:
        cleaned = clean_text(page.text)
        if not cleaned:
            continue
        for piece in splitter.split_text(cleaned):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(Chunk(chunk_index=chunk_index, page_number=page.page_number, text=piece))
            chunk_index += 1

    return chunks


def process_pdf(file_path: str) -> tuple[list[ExtractedPage], list[Chunk]]:
    """Full ingestion: extract -> chunk. Raises PdfExtractionError if unreadable."""
    pages = extract_pages_from_pdf(file_path)
    chunks = chunk_pages(pages)
    return pages, chunks

from app.rag.ingestion import ExtractedPage, chunk_pages, clean_text


def test_clean_text_collapses_blank_lines_and_spaces():
    dirty = "Line one\n\n\n\nLine two   with    spaces\n\n\n"
    cleaned = clean_text(dirty)
    assert "\n\n\n" not in cleaned
    assert "Line two with spaces" in cleaned


def test_clean_text_preserves_numbers_and_percentages():
    dirty = "Minimum attendance is   75%   as of 01/06/2026."
    cleaned = clean_text(dirty)
    assert "75%" in cleaned
    assert "01/06/2026" in cleaned


def test_chunk_pages_tracks_page_numbers():
    pages = [
        ExtractedPage(page_number=1, text="A" * 50),
        ExtractedPage(page_number=2, text="B" * 50),
    ]
    chunks = chunk_pages(pages)
    page_numbers = {c.page_number for c in chunks}
    assert page_numbers == {1, 2}
    assert all(c.text for c in chunks)


def test_chunk_pages_skips_empty_pages():
    pages = [ExtractedPage(page_number=1, text="   \n\n  ")]
    chunks = chunk_pages(pages)
    assert chunks == []

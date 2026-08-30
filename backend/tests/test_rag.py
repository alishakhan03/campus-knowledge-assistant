from unittest.mock import MagicMock, patch

from app.services.rag_service import RAGService


def make_service_with_mocked_vector_store(matches):
    mock_vector_service = MagicMock()
    mock_vector_service.similarity_search.return_value = matches
    with patch("app.services.rag_service.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="Students must maintain at least 75% attendance.")
        mock_llm_cls.return_value = mock_llm_instance
        service = RAGService(mock_vector_service)
    return service, mock_llm_instance


def test_answer_found_within_relevant_context():
    matches = [
        {
            "score": 0.89,
            "document_id": 1,
            "document_title": "Examination Rules",
            "page_number": 4,
            "chunk_index": 0,
            "text": "Students must maintain a minimum attendance of 75%.",
        }
    ]
    service, mock_llm = make_service_with_mocked_vector_store(matches)

    result = service.answer_question("What attendance is required?", history=[])

    assert "75%" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["document_title"] == "Examination Rules"
    mock_llm.invoke.assert_called_once()


def test_no_relevant_context_returns_not_found_message():
    # No matches above RAG_MIN_SCORE at all
    service, mock_llm = make_service_with_mocked_vector_store([])

    result = service.answer_question("What is the hostel menu?", history=[])

    assert "couldn't find this information" in result["answer"]
    assert result["sources"] == []
    mock_llm.invoke.assert_not_called()


def test_low_similarity_matches_are_filtered_out():
    # Matches exist but below the RAG_MIN_SCORE threshold (0.70 default)
    matches = [
        {
            "score": 0.40,
            "document_id": 2,
            "document_title": "Unrelated Circular",
            "page_number": 1,
            "chunk_index": 0,
            "text": "Some unrelated text.",
        }
    ]
    service, mock_llm = make_service_with_mocked_vector_store(matches)

    result = service.answer_question("What is the hostel menu?", history=[])

    assert "couldn't find this information" in result["answer"]
    mock_llm.invoke.assert_not_called()

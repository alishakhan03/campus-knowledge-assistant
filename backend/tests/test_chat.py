from unittest.mock import patch


def register_login(client, email, password="Password123!"):
    client.post("/api/auth/register", json={"name": "User", "email": email, "password": password})
    return client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_access_other_users_conversation(client):
    token_a = register_login(client, "usera@test.com")
    token_b = register_login(client, "userb@test.com")

    conv = client.post("/api/chat/conversations", json={}, headers=auth_header(token_a)).json()

    response = client.get(f"/api/chat/conversations/{conv['id']}", headers=auth_header(token_b))
    assert response.status_code == 404


def test_valid_question_is_processed_with_mocked_rag(client):
    token = register_login(client, "usrag@test.com")
    conv = client.post("/api/chat/conversations", json={}, headers=auth_header(token)).json()

    mocked_result = {
        "answer": "Students must maintain at least 75% attendance.",
        "sources": [
            {"document_id": 1, "document_title": "Examination Regulations 2026", "page_number": 12, "similarity_score": 0.91}
        ],
        "debug": {"retrieved_chunks": []},
    }

    with patch("app.services.chat_service.get_rag_service") as mock_get_service:
        mock_get_service.return_value.answer_question.return_value = mocked_result
        response = client.post(
            f"/api/chat/conversations/{conv['id']}/messages",
            json={"content": "What is the minimum attendance required?"},
            headers=auth_header(token),
        )

    assert response.status_code == 200
    body = response.json()
    assert "75%" in body["message"]["content"]
    assert body["message"]["role"] == "ASSISTANT"

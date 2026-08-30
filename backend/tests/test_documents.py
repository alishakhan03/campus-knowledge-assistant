import io

from app.core.security import hash_password
from app.models.user import User, UserRole


def make_admin_token(client, db_session):
    admin = User(name="Admin", email="admin2@test.com", password_hash=hash_password("AdminPass123!"), role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.commit()
    return client.post(
        "/api/auth/login", json={"email": "admin2@test.com", "password": "AdminPass123!"}
    ).json()["access_token"]


def test_non_pdf_file_rejected(client, db_session):
    token = make_admin_token(client, db_session)
    files = {"file": ("notes.txt", io.BytesIO(b"just text"), "text/plain")}
    data = {"title": "Notes", "category": "GENERAL"}
    response = client.post("/api/documents", files=files, data=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_empty_pdf_rejected(client, db_session):
    token = make_admin_token(client, db_session)
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    data = {"title": "Empty", "category": "GENERAL"}
    response = client.post("/api/documents", files=files, data=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_invalid_category_rejected(client, db_session):
    token = make_admin_token(client, db_session)
    files = {"file": ("rules.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"title": "Rules", "category": "NOT_A_REAL_CATEGORY"}
    response = client.post("/api/documents", files=files, data=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

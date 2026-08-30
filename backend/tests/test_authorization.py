import io

from app.models.user import UserRole


def test_student_cannot_upload_document(client):
    client.post("/api/auth/register", json={"name": "Student", "email": "stud@test.com", "password": "Password123!"})
    token = client.post(
        "/api/auth/login", json={"email": "stud@test.com", "password": "Password123!"}
    ).json()["access_token"]
    files = {"file": ("rules.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"title": "Rules", "category": "GENERAL"}
    response = client.post(
        "/api/documents", files=files, data=data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_admin_can_upload_document(client, db_session):
    from app.core.security import hash_password
    from app.models.user import User

    admin = User(name="Admin", email="admin@test.com", password_hash=hash_password("AdminPass123!"), role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.commit()

    token = client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "AdminPass123!"}
    ).json()["access_token"]

    files = {"file": ("rules.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"title": "Rules", "category": "GENERAL"}
    response = client.post(
        "/api/documents", files=files, data=data, headers={"Authorization": f"Bearer {token}"}
    )
    # Upload succeeds even though background PDF processing will later fail on
    # this fake PDF - that failure is captured as DocumentStatus.FAILED, not a 4xx/5xx here.
    assert response.status_code == 201
    assert response.json()["status"] == "UPLOADED"

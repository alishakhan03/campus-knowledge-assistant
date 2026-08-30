def register(client, email="student@test.com", password="Password123!"):
    return client.post(
        "/api/auth/register", json={"name": "Test Student", "email": email, "password": password}
    )


def login(client, email="student@test.com", password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_register_creates_student(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "STUDENT"
    assert body["email"] == "student@test.com"


def test_register_duplicate_email_rejected(client):
    register(client)
    response = register(client)
    assert response.status_code == 409


def test_login_success_returns_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_password_rejected(client):
    register(client)
    response = login(client, password="WrongPassword!")
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_valid_token(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "student@test.com"

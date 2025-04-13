import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_and_login():
    # Données de test
    user_data = {
        "username": "pytester",
        "email": "pytest@example.com",
        "password": "StrongPass123!"
    }

    # --- Étape 1 : Inscription ---
    register_response = client.post("/register", json=user_data)

    assert register_response.status_code == 200, f"Échec register: {register_response.text}"
    token_data = register_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # --- Étape 2 : Connexion ---
    login_payload = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    login_response = client.post("/login", json=login_payload)

    assert login_response.status_code == 200, f"Échec login: {login_response.text}"
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

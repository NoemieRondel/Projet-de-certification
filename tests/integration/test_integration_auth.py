import pytest
from fastapi.testclient import TestClient
import uuid
import sys
import os

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

client = TestClient(app)


def test_full_auth_flow_integration():
    """Test d'intégration complet de l'authentification : register -> login -> accès route protégée"""

    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    unique_username = f"user_{uuid.uuid4().hex[:6]}"
    password = "StrongPass123!"

    # Étape 1 - Inscription
    register_response = client.post("/auth/register", json={
        "username": unique_username,
        "email": unique_email,
        "password": password
    })
    assert register_response.status_code in [200, 201], f"Register failed: {register_response.text}"

    # Étape 2 - Connexion
    login_response = client.post("/auth/login", json={
        "email": unique_email,
        "password": password
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    data = login_response.json()
    assert "access_token" in data

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Étape 3 - Accès à une route protégée
    protected_response = client.get("/articles/", headers=headers)
    assert protected_response.status_code in [200, 404], f"Access to protected route failed: {protected_response.text}"

    # Bonus : on peut aussi vérifier que le token n'est pas vide ou invalide
    assert len(token) > 10

import pytest
from fastapi.testclient import TestClient
import uuid
import sys
import os

# Ajout du chemin racine du projet au sys.path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

client = TestClient(app)


def create_temp_user_and_get_token():
    """Helper pour créer un utilisateur temporaire et récupérer un token."""
    email = f"scientificuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPassword123!"

    # Register
    register_response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code in [200, 201], f"Register failed: {register_response.text}"

    # Login
    login_response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]

    return token


@pytest.fixture(scope="module")
def auth_token():
    """Fixture pour obtenir un token une seule fois pour tous les tests du module."""
    return create_temp_user_and_get_token()


def test_get_trending_keywords(auth_token):
    """Test GET /trends/keywords pour récupérer les mots-clés tendances."""
    params = {
        "last_days": 30,
        "limit": 10,
        "offset": 0
    }
    response = client.get(
        "/trends/keywords",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )

    assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code} - {response.text}"

    if response.status_code == 200:
        data = response.json()
        assert "trending_keywords" in data, "Key 'trending_keywords' not found in response."
        assert isinstance(data["trending_keywords"], list), "'trending_keywords' should be a list."

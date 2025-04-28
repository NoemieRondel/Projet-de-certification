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
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
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


def test_get_user_preferences_success():
    """Test pour récupérer les préférences utilisateur."""
    token = create_temp_user_and_get_token()

    response = client.get(
        "/preferences/user-preferences",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200, f"Unexpected status: {response.status_code} - {response.text}"
    data = response.json()

    # Vérifie que la réponse contient bien les clés attendues
    assert "user_preferences" in data, "Missing 'user_preferences' key in response"
    assert "available_filters" in data, "Missing 'available_filters' key in response"

    user_preferences = data["user_preferences"]
    available_filters = data["available_filters"]

    # Vérifie que les préférences utilisateur sont des listes
    assert isinstance(user_preferences.get("source_preferences", []), list), "source_preferences should be a list"
    assert isinstance(user_preferences.get("video_channel_preferences", []), list), "video_channel_preferences should be a list"
    assert isinstance(user_preferences.get("keyword_preferences", []), list), "keyword_preferences should be a list"

    # Vérifie que les filtres disponibles sont bien présents et sont des listes
    assert isinstance(available_filters.get("articles", []), list), "articles should be a list"
    assert isinstance(available_filters.get("videos", []), list), "videos should be a list"
    assert isinstance(available_filters.get("keywords", []), list), "keywords should be a list"

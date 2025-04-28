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


def test_get_all_videos_success_or_empty():
    """Test pour récupérer toutes les vidéos avec ou sans filtres."""
    token = create_temp_user_and_get_token()

    response = client.get(
        "/videos/",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Selon la base, il peut y avoir des vidéos ou pas
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"

    if response.status_code == 200:
        videos = response.json()
        assert isinstance(videos, list), "La réponse doit être une liste"
        for video in videos:
            assert "id" in video
            assert "title" in video
            assert "video_url" in video
            assert "source" in video
            assert "publication_date" in video
            assert isinstance(video["publication_date"], str), "publication_date doit être une string formatée"

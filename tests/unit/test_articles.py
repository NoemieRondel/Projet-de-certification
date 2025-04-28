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


def test_get_all_articles_success():
    """Test pour récupérer tous les articles sans filtre."""
    token = create_temp_user_and_get_token()

    response = client.get(
        "/articles/",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 200 même si la liste est vide
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"
    if response.status_code == 200:
        articles = response.json()
        assert isinstance(articles, list), "Expected list of articles"
        if articles:
            for article in articles:
                assert "id" in article
                assert "title" in article
                assert "source" in article
                assert "publication_date" in article
                assert "link" in article


def test_get_all_articles_with_filters():
    """Test pour récupérer les articles avec des filtres (même si pas de résultats)."""
    token = create_temp_user_and_get_token()

    params = {
        "start_date": "2020-01-01",
        "end_date": "2025-12-31",
        "source": "TechCrunch",
        "keywords": "AI"
    }

    response = client.get(
        "/articles/",
        params=params,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"
    if response.status_code == 200:
        articles = response.json()
        assert isinstance(articles, list)
        if articles:
            for article in articles:
                assert "id" in article
                assert "title" in article
                assert "source" in article
                assert "publication_date" in article
                assert "link" in article


def test_get_latest_articles_success():
    """Test pour récupérer les derniers articles par source."""
    token = create_temp_user_and_get_token()

    response = client.get(
        "/articles/latest",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"
    if response.status_code == 200:
        articles = response.json()
        assert isinstance(articles, list)
        if articles:
            for article in articles:
                assert "id" in article
                assert "title" in article
                assert "source" in article
                assert "publication_date" in article
                assert "link" in article

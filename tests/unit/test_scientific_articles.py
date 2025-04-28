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


def test_get_all_scientific_articles_no_filters(auth_token):
    """Test GET /scientific-articles sans filtres."""
    response = client.get(
        "/scientific-articles/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code} - {response.text}"
    if response.status_code == 200:
        articles = response.json()
        assert isinstance(articles, list)
        for article in articles:
            assert "id" in article
            assert "title" in article
            assert "article_url" in article
            assert "publication_date" in article


def test_get_all_scientific_articles_with_filters(auth_token):
    """Test GET /scientific-articles avec filtres (par auteur et mots-clés)."""
    params = {
        "authors": "John Doe",
        "keywords": "AI, Machine Learning"
    }
    response = client.get(
        "/scientific-articles/",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )
    assert response.status_code in [200, 404], f"Unexpected status code: {response.status_code} - {response.text}"
    if response.status_code == 200:
        articles = response.json()
        assert isinstance(articles, list)
        for article in articles:
            assert "id" in article
            assert "title" in article
            assert "article_url" in article
            assert "publication_date" in article


def test_get_all_scientific_articles_with_invalid_date(auth_token):
    """Test GET /scientific-articles avec une date invalide."""
    params = {
        "start_date": "2024-13-01"  # Mois invalide
    }
    response = client.get(
        "/scientific-articles/",
        headers={"Authorization": f"Bearer {auth_token}"},
        params=params
    )
    assert response.status_code == 400, f"Expected 400 for invalid date, got {response.status_code}"
    data = response.json()
    assert "detail" in data
    assert "Format de date invalide" in data["detail"]

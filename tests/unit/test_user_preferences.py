import os 
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
import json

# Ajout du chemin du projet
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app as fastapi_app
from app.security.jwt_handler import create_access_token  # Fonction pour créer un token JWT


# Générer un token d'authentification pour un utilisateur
@pytest.fixture
def auth_header():
    # Simuler la création d'un utilisateur et l'authentification
    user = {"user_id": 1}  # Utilisateur fictif avec user_id 1
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


# Test de la route GET /user-preferences
def test_get_user_preferences(auth_header):
    client = TestClient(fastapi_app)

    response = client.get("/user-preferences", headers=auth_header)

    assert response.status_code == 200
    data = response.json()
    assert "user_preferences" in data
    assert "available_filters" in data
    assert isinstance(data["user_preferences"], dict)
    assert isinstance(data["available_filters"], dict)
    assert "articles" in data["available_filters"]
    assert "videos" in data["available_filters"]
    assert "keywords" in data["available_filters"]


# Test de la route POST /user-preferences
def test_update_user_preferences(auth_header):
    client = TestClient(fastapi_app)

    preferences = {
        "source_preferences": ["TechCrunch", "Wired"],
        "video_channel_preferences": ["YouTube", "Vimeo"],
        "keyword_preferences": ["AI", "ML", "Data Science"]
    }

    response = client.post(
        "/user-preferences",
        headers=auth_header,
        json=preferences
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Préférences mises à jour avec succès"}


# Test de la route DELETE /user-preferences
def test_delete_user_preferences(auth_header):
    client = TestClient(fastapi_app)

    preferences_to_delete = {
        "source_preferences": ["TechCrunch"],
        "video_channel_preferences": ["YouTube"],
        "keyword_preferences": ["AI"]
    }

    response = client.delete(
        "/user-preferences",
        headers=auth_header,
        json=preferences_to_delete
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Préférences mises à jour après suppression"}


# Test pour une requête DELETE sans préférences
def test_delete_all_user_preferences(auth_header):
    client = TestClient(fastapi_app)

    response = client.delete(
        "/user-preferences",
        headers=auth_header,
        json={}
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Préférences mises à jour après suppression"}


# Test de la route GET /user-preferences avec un utilisateur non authentifié
def test_get_user_preferences_unauthenticated():
    client = TestClient(fastapi_app)

    response = client.get("/user-preferences")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token: user_id not found"}


# Test de la route POST /user-preferences avec un utilisateur non authentifié
def test_update_user_preferences_unauthenticated():
    client = TestClient(fastapi_app)

    preferences = {
        "source_preferences": ["TechCrunch", "Wired"],
        "video_channel_preferences": ["YouTube", "Vimeo"],
        "keyword_preferences": ["AI", "ML", "Data Science"]
    }

    response = client.post(
        "/user-preferences",
        json=preferences
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token: user_id not found"}

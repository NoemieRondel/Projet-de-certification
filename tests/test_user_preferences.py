import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt():
    with patch("app.user_preferences_route.jwt_required", return_value={"user_id": 1}):
        yield


@patch("app.user_preferences_route.get_available_filters")
@patch("app.user_preferences_route.get_connection")
def test_get_user_preferences(mock_get_connection, mock_get_filters, mock_jwt):
    mock_get_filters.return_value = {
        "articles": ["The Verge", "TechCrunch"],
        "videos": ["OpenAI"],
        "keywords": ["AI", "Deep Learning"]
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = {
        "source_preferences": "The Verge;TechCrunch",
        "video_channel_preferences": "OpenAI",
        "keyword_preferences": "AI;Deep Learning"
    }

    with patch("app.user_preferences_route.jwt_required", return_value={"user_id": 1}):
        response = client.get("/user-preferences")

    assert response.status_code == 200
    data = response.json()
    assert data["user_preferences"]["source_preferences"] == ["The Verge", "TechCrunch"]


@patch("app.user_preferences_route.get_available_filters")
@patch("app.user_preferences_route.get_connection")
def test_post_user_preferences(mock_get_connection, mock_get_filters, mock_jwt):
    mock_get_filters.return_value = {
        "articles": ["The Verge", "TechCrunch"],
        "videos": ["OpenAI"],
        "keywords": ["AI", "Deep Learning"]
    }

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = None  # simulate no existing prefs

    with patch("app.user_preferences_route.jwt_required", return_value={"user_id": 1}):
        response = client.post("/user-preferences", json={
            "source_preferences": ["The Verge"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        })

    assert response.status_code == 200
    assert response.json()["message"] == "Préférences mises à jour avec succès"


@patch("app.user_preferences_route.get_connection")
def test_delete_user_preferences(mock_get_connection, mock_jwt):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = {
        "source_preferences": "The Verge;TechCrunch",
        "video_channel_preferences": "OpenAI",
        "keyword_preferences": "AI;Deep Learning"
    }

    with patch("app.user_preferences_route.jwt_required", return_value={"user_id": 1}):
        response = client.delete("/user-preferences", json={
            "source_preferences": ["TechCrunch"]
        })

    assert response.status_code == 200
    assert response.json()["message"] == "Préférences mises à jour après suppression"

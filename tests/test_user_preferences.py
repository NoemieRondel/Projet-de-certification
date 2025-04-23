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


class TestUserPreferences:

    from app.main import app

    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.user_preferences_route.get_available_filters")
    @patch("app.database.get_connection")
    def test_get_user_preferences(self, mock_get_connection, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_cursor.fetchone.return_value = {
            "source_preferences": "The Verge;TechCrunch",
            "video_channel_preferences": "OpenAI",
            "keyword_preferences": "AI;Deep Learning"
        }

        response = self.client.get("/user-preferences")

        assert response.status_code == 200
        data = response.json()

        assert "user_preferences" in data

        assert data["user_preferences"]["source_preferences"] == ["The Verge", "TechCrunch"]


        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.user_preferences_route.get_available_filters")
    @patch("app.database.get_connection")
    def test_post_user_preferences(self, mock_get_connection, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_cursor.fetchone.return_value = None
        mock_cursor.execute.return_value = None

        payload = {
            "source_preferences": ["The Verge"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        }

        response = self.client.post("/user-preferences", json=payload)

        assert response.status_code == 200
        assert response.json()["message"] == "Préférences mises à jour avec succès"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_delete_user_preferences(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler les préférences existantes avant la suppression
        mock_cursor.fetchone.return_value = {
            "source_preferences": "The Verge;TechCrunch",
            "video_channel_preferences": "OpenAI",
            "keyword_preferences": "AI;Deep Learning"
        }
        mock_cursor.execute.return_value = None

        payload = {
            "source_preferences": ["TechCrunch"]
        }

        response = self.client.delete("/user-preferences", json=payload)

        assert response.status_code == 200
        assert response.json()["message"] == "Préférences mises à jour après suppression"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

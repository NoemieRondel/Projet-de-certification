import os
import sys
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app as fastapi_app
from app.security.jwt_handler import jwt_required


def mock_jwt_required_func():
    return {"user_id": 1}


class TestUserPreferences:
    app = fastapi_app 
    client = TestClient(app)

    @pytest.fixture(autouse=True, scope="class")
    def setup_class_auth_override(self):
        original_override = self.app.dependency_overrides.get(jwt_required)
        self.app.dependency_overrides[jwt_required] = mock_jwt_required_func

        yield

        if original_override:
             self.app.dependency_overrides[jwt_required] = original_override
        else:
             del self.app.dependency_overrides[jwt_required]

    @patch("app.routes.user_preferences.get_available_filters")
    @patch("app.database.connection_pool")
    def test_get_user_preferences(self, mock_pool, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.get_connection.return_value = mock_conn

        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_cursor.fetchone.return_value = {
            "source_preferences": "The Verge;TechCrunch",
            "video_channel_preferences": "OpenAI",
            "keyword_preferences": "AI;Deep Learning"
        }

        response = self.client.get("/preferences/user-preferences")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()

        assert "user_preferences" in data
        assert "available_filters" in data
        assert data["user_preferences"]["source_preferences"] == ["The Verge", "TechCrunch"]
        assert data["available_filters"]["articles"] == ["The Verge", "TechCrunch"]

        mock_get_filters.assert_called_once()
        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.routes.user_preferences.get_available_filters")
    @patch("app.database.connection_pool")
    def test_post_user_preferences(self, mock_pool, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None
        mock_conn.close.return_value = None

        mock_cursor.fetchone.return_value = None

        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        payload = {
            "source_preferences": ["The Verge"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        }

        response = self.client.post("/preferences/user-preferences", json=payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json()["message"] == "Préférences mises à jour avec succès"

        mock_get_filters.assert_called_once()
        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_delete_user_preferences(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None
        mock_conn.close.return_value = None

        mock_cursor.fetchone.return_value = {
            "source_preferences": "The Verge;TechCrunch",
            "video_channel_preferences": "OpenAI",
            "keyword_preferences": "AI;Deep Learning"
        }
        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        payload = {
            "source_preferences": ["TechCrunch"]
        }

        response = self.client.delete(
            "/preferences/user-preferences",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json()["message"] == "Préférences mises à jour après suppression"

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_delete_user_preferences_not_found(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_cursor.fetchone.return_value = None

        payload = {
            "source_preferences": ["TechCrunch"]
        }

        response = self.client.delete(
            "/preferences/user-preferences",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}. Response: {response.text}"
        assert response.json()["detail"] == "Aucune préférence trouvée pour cet utilisateur."

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_not_called()
        mock_conn.rollback.assert_not_called()
        mock_conn.close.assert_called_once()

    @patch("app.routes.user_preferences.get_available_filters")
    @patch("app.database.connection_pool")
    def test_post_user_preferences_invalid_value(self, mock_pool, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        payload = {
            "source_preferences": ["Invalid Source"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        }

        response = self.client.post("/preferences/user-preferences", json=payload)

        assert response.status_code == 400, f"Expected 400, got {response.status_code}. Response: {response.text}"

        mock_get_filters.assert_called_once()
        mock_pool.get_connection.assert_not_called()

    @patch("app.routes.user_preferences.get_available_filters")
    @patch("app.database.connection_pool")
    def test_delete_user_preferences_invalid_value(self, mock_pool, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        payload = {
            "source_preferences": ["Invalid Source"]
        }

        response = self.client.delete(
            "/preferences/user-preferences",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400, f"Expected 400, got {response.status_code}. Response: {response.text}"

        mock_get_filters.assert_called_once()
        mock_pool.get_connection.assert_not_called()

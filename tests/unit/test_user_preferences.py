import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestUserPreferences:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        # Vérifier ce chemin de patch pour jwt_required
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

        # Simuler le retour de la base pour les préférences utilisateur
        mock_cursor.fetchone.return_value = {
            "source_preferences": "The Verge;TechCrunch",
            "video_channel_preferences": "OpenAI",
            "keyword_preferences": "AI;Deep Learning"
        }

        response = self.client.get("/preferences/user-preferences")

        assert response.status_code == 200
        data = response.json()

        assert "user_preferences" in data
        assert "available_filters" in data
        assert data["user_preferences"]["source_preferences"] == ["The Verge", "TechCrunch"]
        assert data["available_filters"]["articles"] == ["The Verge", "TechCrunch"]

        mock_get_filters.assert_called_once()
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

        # Simuler que la requête INSERT ou UPDATE réussit
        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        payload = {
            "source_preferences": ["The Verge"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        }

        response = self.client.post("/preferences/user-preferences", json=payload)

        assert response.status_code == 200
        assert response.json()["message"] == "Préférences mises à jour avec succès"

        mock_get_filters.assert_called_once()
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        assert mock_cursor.execute.call_count == 2
        mock_cursor.fetchone.assert_called_once()
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
        # Simuler que la requête UPDATE ou DELETE réussit
        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        payload = {
            "source_preferences": ["TechCrunch"]
        }

        response = self.client.delete("/preferences/user-preferences", json=payload)

        assert response.status_code == 200
        assert response.json()["message"] == "Préférences mises à jour après suppression"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        assert mock_cursor.execute.call_count == 2
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_delete_user_preferences_not_found(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler qu'aucune préférence n'est trouvée pour la suppression
        mock_cursor.fetchone.return_value = None

        payload = {
            "source_preferences": ["TechCrunch"]
        }

        response = self.client.delete("/preferences/user-preferences", json=payload)

        assert response.status_code == 404
        assert response.json()["detail"] == "Aucune préférence trouvée pour cet utilisateur." # Vérifier le message exact

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    # Ajouter des tests pour la validation des préférences (statut 400)
    @patch("app.user_preferences_route.get_available_filters")
    @patch("app.database.get_connection")
    def test_post_user_preferences_invalid_value(self, mock_get_connection, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        # Simuler un payload avec une valeur non valide
        payload = {
            "source_preferences": ["Invalid Source"],
            "video_channel_preferences": ["OpenAI"],
            "keyword_preferences": ["AI"]
        }

        response = self.client.post("/preferences/user-preferences", json=payload)

        assert response.status_code == 400
        assert "Valeurs non valides pour source_preferences" in response.json()["detail"] # Vérifier le message d'erreur

        mock_get_filters.assert_called_once()
        mock_cursor = mock_get_connection.return_value.cursor.return_value.__enter__.return_value # Accéder au mock cursor
        assert mock_cursor.execute.call_count == 0
        assert mock_cursor.fetchone.call_count == 0
        assert mock_cursor.fetchall.call_count == 0
        mock_get_connection.return_value.commit.assert_not_called()

    @patch("app.user_preferences_route.get_available_filters")
    @patch("app.database.get_connection")
    def test_delete_user_preferences_invalid_value(self, mock_get_connection, mock_get_filters):
        mock_get_filters.return_value = {
            "articles": ["The Verge", "TechCrunch"],
            "videos": ["OpenAI"],
            "keywords": ["AI", "Deep Learning"]
        }

        # Simuler un payload avec une valeur non valide
        payload = {
            "source_preferences": ["Invalid Source"]
        }

        response = self.client.delete("/preferences/user-preferences", json=payload)

        assert response.status_code == 400
        assert "Valeurs non valides pour source_preferences" in response.json()["detail"] # Vérifier le message d'erreur

        mock_get_filters.assert_called_once()
        mock_cursor = mock_get_connection.return_value.cursor.return_value.__enter__.return_value
        assert mock_cursor.execute.call_count == 0
        assert mock_cursor.fetchone.call_count == 0
        assert mock_cursor.fetchall.call_count == 0
        mock_get_connection.return_value.commit.assert_not_called()

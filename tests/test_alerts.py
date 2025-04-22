import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import sys
import os

# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ==============================================================================
# IMPORTANT : Simuler l'initialisation du pool de connexion AVANT d'importer app.main


@patch('mysql.connector.pooling.MySQLConnectionPool')
class TestUserPreferences:
# ==============================================================================

    # Importez app.main après avoir appliqué le patch au niveau de la classe
    from app.main import app

    @pytest.fixture(autouse=True)
    def mock_jwt_required(self): 
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}) as mock:
            yield mock

    @patch("app.database.get_connection")
    @pytest.mark.asyncio
    async def test_update_user_preferences_success(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_get_connection.return_value = mock_conn

        mock_cursor.execute.return_value = None

        payload = {
            "source_preferences": "TechCrunch;The Verge",
            "video_channel_preferences": "DeepLearningAI",
            "keyword_preferences": "AI;ML;NLP"
        }

        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.put("/preferences/1/filters", json=payload)

        assert response.status_code == 200
        assert response.json()["message"] == "Préférences de filtrage mises à jour avec succès."

        # Assertions for database interaction
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    @pytest.mark.asyncio
    async def test_update_user_preferences_db_error(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        payload = {
            "source_preferences": "TechCrunch",
            "video_channel_preferences": "AI_Channels",
            "keyword_preferences": "GPT"
        }

        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.put("/preferences/1/filters", json=payload)

        assert response.status_code == 500
        assert "Erreur interne" in response.json()["detail"]
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection", return_value=None)
    @pytest.mark.asyncio
    async def test_update_user_preferences_connection_error(self, mock_get_connection):
        payload = {
            "source_preferences": "TechCrunch",
            "video_channel_preferences": "AI_Channels",
            "keyword_preferences": "GPT"
        }

        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.put("/preferences/1/filters", json=payload)

        assert response.status_code == 500
        assert response.json()["detail"] == "Impossible de se connecter à la base de données."
        mock_get_connection.assert_called_once()

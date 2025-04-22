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

# ==============================================================================
# IMPORTANT : Simuler l'initialisation du pool de connexion AVANT d'importer app.main


@patch('mysql.connector.pooling.MySQLConnectionPool')
class TestUserDelete:
# ==============================================================================

    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}) as mock:
             yield mock

    # ==========================================================================
    # CORRECTION : Ajout de 'mock_pool' dans la signature pour recevoir le mock du patch de classe
    @patch("app.database.get_connection")
    @patch("app.user_delete_route.decode_jwt_token")
    def test_delete_me_success(self, mock_pool, mock_get_connection, mock_decode_jwt_token):
    # ==========================================================================
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.rowcount = 1
        mock_cursor.execute.return_value = None
        # Simuler un token d’auth
        headers = {"Authorization": "Bearer fake-token"}

        mock_decode_jwt_token.return_value = {"user_id": 1}

        response = self.client.delete("/me", headers=headers)

        assert response.status_code == 200
        assert response.json() == {"message": "Utilisateur supprimé avec succès"}

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_decode_jwt_token.assert_called_once_with("fake-token")
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestUserDelete:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection")
    def test_delete_me_success(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler que les requêtes DELETE réussissent
        mock_cursor.rowcount = 1
        mock_cursor.execute.return_value = None

        headers = {"Authorization": "Bearer fake-token"}

        response = self.client.delete("/users/me", headers=headers)

        assert response.status_code == 200
        # Vérifier le message de succès exact
        assert response.json()["message"] == "Votre compte a été supprimé avec succès."

        # Vérifications de l'interaction simulée avec la base de données
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        assert mock_cursor.execute.call_count == 2
        # Vérifier que commit est appelé une fois
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

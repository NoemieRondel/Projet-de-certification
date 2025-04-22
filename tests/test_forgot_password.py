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
class TestForgotPassword:
# ==============================================================================

    from app.main import app
    client = TestClient(app)

    @pytest.fixture
    def fake_email(self):
        return "testuser@example.com"

    # ==========================================================================
    @patch("app.database.get_connection")
    @patch("app.mailer.send_email")
    def test_forgot_password_existing_user(self, mock_pool, mock_send_email, mock_get_connection, fake_email):
    # ==========================================================================
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler un utilisateur trouvé en base (fetchone)
        mock_cursor.fetchone.return_value = {"id": 1}

        assert isinstance(fake_email, str), "fake_email fixture did not inject a string"

        response = self.client.post("/forgot_password", json={"email": fake_email})

        assert response.status_code == 200
        assert "message" in response.json()
        assert "un lien de réinitialisation a été envoyé" in response.json()["message"]

        # Vérifier les mocks ont été appelés
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_send_email.assert_called_once()

    # ==========================================================================
    @patch("app.database.get_connection")
    @patch("app.mailer.send_email")
    def test_forgot_password_non_existing_user(self, mock_pool, mock_send_email, mock_get_connection, fake_email):
    # ==========================================================================
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler aucun utilisateur trouvé
        mock_cursor.fetchone.return_value = None

        assert isinstance(fake_email, str), "fake_email fixture did not inject a string"

        response = self.client.post("/forgot_password", json={"email": fake_email})

        assert response.status_code == 200
        assert "message" in response.json()
        assert "un lien de réinitialisation a été envoyé" in response.json()["message"]

        # Vérifier les mocks ont été appelés
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_send_email.assert_not_called()

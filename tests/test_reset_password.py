import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
import datetime

# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestResetPassword:

    from app.main import app
    client = TestClient(app)

    @patch("app.database.get_connection")
    @patch("app.security.password_handler.hash_password")
    def test_reset_password_success(self, mock_get_connection, mock_hash_password):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "expires_at": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }

        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        mock_hash_password.return_value = "fake_hashed_password"

        response = self.client.post(
            "/reset_password/fake-token",
            json={"new_password": "super_secure_pass123!"}
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Mot de passe réinitialisé avec succès"}

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_hash_password.assert_called_once_with("super_secure_pass123!")

    @patch("app.database.get_connection")
    def test_reset_password_invalid_token(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_cursor.fetchone.return_value = None

        response = self.client.post("/reset_password/invalid-token", json={"new_password": "pass"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Token invalide ou expiré"

        # Vérifier l'interaction avec la base de données
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_reset_password_expired_token(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler un token expiré
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "expires_at": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }

        response = self.client.post("/reset_password/expired-token", json={"new_password": "pass"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Token expiré"

        # Vérifier l'interaction avec la base de données
        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

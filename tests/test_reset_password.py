import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
import datetime
import bcrypt

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestResetPassword:
    from app.main import app
    client = TestClient(app)

    @patch("app.database.get_connection")
    @patch("bcrypt.hashpw", return_value=b"fake_hashed_password")
    @patch("datetime.datetime")
    def test_reset_password_success(self, mock_datetime, mock_hashpw, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler la date actuelle pour le test d'expiration
        now = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        # Simuler un token trouvé en base et non expiré
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "expires_at": now + datetime.timedelta(hours=1)
        }

        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        new_password = "super_secure_pass123!"

        response = self.client.post(
            "/auth/reset_password/fake-token",
            json={"new_password": new_password}
        )

        assert response.status_code == 200
        assert response.json() == {"message": "Mot de passe réinitialisé avec succès"}

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.fetchone.assert_called_once()

        calls = mock_cursor.execute.call_args_list
        assert len(calls) == 3

        mock_conn.commit.assert_called()
        mock_conn.close.assert_called_once()

        # Vérifier que bcrypt.hashpw a été appelé avec le nouveau mot de passe encodé
        mock_hashpw.assert_called_once_with(new_password.encode("utf-8"), bcrypt.gensalt())

    @patch("app.database.get_connection")
    @patch("datetime.datetime")
    def test_reset_password_invalid_token(self, mock_datetime, mock_get_connection):
        # Simuler la date actuelle
        mock_datetime.utcnow.return_value = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.timedelta = datetime.timedelta

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler aucun token trouvé
        mock_cursor.fetchone.return_value = None

        response = self.client.post("/auth/reset_password/invalid-token", json={"new_password": "pass"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Token invalide ou expiré"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    @patch("datetime.datetime")
    def test_reset_password_expired_token(self, mock_datetime, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler la date actuelle
        now = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        # Simuler un token trouvé mais expiré
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "expires_at": now - datetime.timedelta(hours=1)
        }

        # Simuler que la requête DELETE réussit
        mock_cursor.execute.return_value = None
        mock_cursor.rowcount = 1

        response = self.client.post("/auth/reset_password/expired-token", json={"new_password": "pass"})

        assert response.status_code == 400
        assert response.json()["detail"] == "Token expiré"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        calls = mock_cursor.execute.call_args_list
        assert len(calls) == 2

        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

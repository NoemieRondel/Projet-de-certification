import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestForgotPassword:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture
    def fake_email(self):
        return "testuser@example.com"

    @patch("app.database.get_connection")
    @patch("app.mailer.send_email")
    @patch("secrets.token_urlsafe", return_value="fake-reset-token")
    @patch("datetime.datetime")
    def test_forgot_password_existing_user(self, mock_datetime, mock_token_urlsafe, mock_send_email, mock_get_connection, fake_email):
        mock_datetime.utcnow.return_value = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.timedelta = datetime.timedelta

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler un utilisateur trouvé en base
        mock_cursor.fetchone.return_value = {"id": 1}

        assert isinstance(fake_email, str), "fake_email fixture did not inject a string"

        response = self.client.post("/auth/forgot_password", json={"email": fake_email})

        assert response.status_code == 200
        assert "message" in response.json()
        assert "un lien de réinitialisation a été envoyé" in response.json()["message"]

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()

        mock_cursor.execute.assert_called()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_token_urlsafe.assert_called_once_with(32)
        # Vérifier que l'email est envoyé avec les bons arguments
        mock_send_email.assert_called_once_with(
            to_email=fake_email,
            subject="Réinitialisation de votre mot de passe",
            body=f"Bonjour,\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe : http://127.0.0.1:5000/reset_password/fake-reset-token\n\nCe lien expire dans 1 heure."
        )

    @patch("app.database.get_connection")
    @patch("app.mailer.send_email")
    def test_forgot_password_non_existing_user(self, mock_send_email, mock_get_connection, fake_email):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        # Simuler aucun utilisateur trouvé
        mock_cursor.fetchone.return_value = None

        assert isinstance(fake_email, str), "fake_email fixture did not inject a string"

        response = self.client.post("/auth/forgot_password", json={"email": fake_email})

        assert response.status_code == 200
        assert "message" in response.json()
        assert "un lien de réinitialisation a été envoyé" in response.json()["message"] # Vérifier le message exact

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_conn.close.assert_called_once()

        mock_send_email.assert_not_called()

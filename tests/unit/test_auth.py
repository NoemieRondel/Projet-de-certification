import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app


class TestAuth:
    @pytest.mark.unit
    @patch("app.database.connection_pool")
    @patch("app.security.password_handler.hash_password")
    @patch("app.security.password_handler.verify_password")
    @patch("app.security.jwt_handler.create_access_token")
    def test_register_and_login(
        self,
        mock_create_access_token,
        mock_verify_password,
        mock_hash_password,
        mock_pool
    ):
        client = TestClient(app)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.get_connection.return_value = mock_conn

        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_conn.commit.return_value = None
        mock_conn.rollback.return_value = None
        mock_conn.close.return_value = None

        # Simule que l'email est déjà utilisé (renvoie un utilisateur existant)
        mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "username": "pytester",
                "email": "pytest@example.com",
                "password_hash": "fake_hashed_password"
            },  # Simule un email déjà utilisé
            None,
            None,
            None
        ]

        # Simule le résultat des opérations qui modifient des lignes
        mock_cursor.rowcount = 1
        mock_cursor.lastrowid = 1
        # Mock les méthodes de password handler et jwt handler
        mock_hash_password.return_value = "fake_hashed_password"
        mock_verify_password.return_value = True
        mock_create_access_token.return_value = "fake_jwt_token"

        user_data = {
            "username": "pytester",
            "email": "pytest@example.com",
            "password": "StrongPass123!"
        }

        # Test Enregistrement (email déjà pris)
        res_register = client.post("/auth/register", json=user_data)
        assert res_register.status_code == 400, f"Registration failed with status {res_register.status_code}. Response: {res_register.text}"
        assert res_register.json() == {"detail": "Email déjà utilisé."}, f"Unexpected response: {res_register.json()}"

        # Test Enregistrement avec un email unique
        user_data_unique = {
            "username": "pytester2",
            "email": "pytester2@example.com",
            "password": "StrongPass123!"
        }
        res_register_unique = client.post("/auth/register", json=user_data_unique)
        assert res_register_unique.status_code == 200, f"Registration failed with status {res_register_unique.status_code}. Response: {res_register_unique.text}"

        # Test Connexion
        login_data = {
            "email": "pytester2@example.com",
            "password": "StrongPass123!"
        }
        res_login = client.post("/auth/login", json=login_data)

        assert res_login.status_code == 200, f"Login failed with status {res_login.status_code}. Response: {res_login.text}"
        login_response_data = res_login.json()
        assert "access_token" in login_response_data, f"Login response missing access_token. Response: {login_response_data}"
        assert login_response_data["access_token"] == "fake_jwt_token"

        # Vérifications des appels aux mocks
        mock_pool.get_connection.call_count == 2
        mock_cursor.execute.call_count >= 2
        mock_cursor.fetchone.call_count == 2
        mock_conn.commit.call_count == 1
        mock_conn.close.call_count == 2

        mock_hash_password.assert_called_once_with("StrongPass123!")
        mock_verify_password.assert_called_once_with("StrongPass123!", "fake_hashed_password")
        mock_create_access_token.assert_called_once()

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


class TestAuth:

    from app.main import app
    client = TestClient(app)

    @patch("app.database.get_connection")
    @patch("app.security.password_handler.hash_password")
    @patch("app.security.password_handler.verify_password")
    def test_register_and_login(self, mock_get_connection, mock_hash_password, mock_verify_password):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        def mock_execute_side_effect(query, params=None):
            if "INSERT INTO users" in query:
                mock_cursor.rowcount = 1
                mock_cursor.lastrowid = 1
            elif "SELECT" in query and "email" in query:
                executed_queries = [call[0][0] for call in mock_cursor.execute.call_args_list]

                if "INSERT INTO users" not in " ".join(executed_queries):
                    mock_cursor.fetchone.return_value = None
                else:
                    mock_cursor.fetchone.return_value = {"id": 1, "username": "pytester", "email": "pytest@example.com", "hashed_password": "fake_hashed_password"}

            else:
                mock_cursor.fetchone.return_value = None
                mock_cursor.fetchall.return_value = []
                mock_cursor.rowcount = 0

        mock_cursor.execute.side_effect = mock_execute_side_effect

        mock_hash_password.return_value = "fake_hashed_password"
        mock_verify_password.return_value = True

        # Données de test
        user_data = {
            "username": "pytester",
            "email": "pytest@example.com",
            "password": "StrongPass123!"
        }

        # Etape 1 : Inscription
        register_response = self.client.post("/register", json=user_data)

        assert register_response.status_code == 200, f"Échec register: {register_response.text}"
        token_data = register_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Etape 2 : Connexion
        login_payload = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        login_response = self.client.post("/login", json=login_payload)

        assert login_response.status_code == 200, f"Échec login: {login_response.text}"
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"

        mock_hash_password.assert_called_once_with(user_data["password"])
        mock_verify_password.assert_called_once_with(login_payload["password"], "fake_hashed_password")

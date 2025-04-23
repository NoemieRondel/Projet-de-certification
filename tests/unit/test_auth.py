import os
import sys
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.mark.unit
@patch("app.database.connection_pool")
@patch("app.security.password_handler.hash_password")
@patch("app.security.password_handler.verify_password")
def test_register_and_login(mock_verify_password, mock_hash_password, mock_pool):
    client = TestClient(app)

    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_pool.get_connection.return_value = mock_conn

    # Configuration du curseur mocké
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    # Mocks pour les méthodes de connexion appelées
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None

    def execute_side_effect(query, params=None):
        query = query.lower()
        # Simule le SELECT utilisateur (pour check existence ou login)
        if "select" in query and "from users" in query and "email" in query:
            if params and user_data["email"] in params:
                return {
                     "id": 1,
                     "username": "pytester",
                     "email": user_data["email"],
                     "password_hash": "fake_hashed_password"
                 }
            else:
                return None
        elif "insert into users" in query:
            mock_cursor.rowcount = 1
            mock_cursor.lastrowid = 1

    mock_cursor.execute.side_effect = execute_side_effect

    mock_hash_password.return_value = "fake_hashed_password"
    mock_verify_password.return_value = True

    user_data = {
        "username": "pytester",
        "email": "pytest@example.com",
        "password": "StrongPass123!"
    }

    # Test Enregistrement
    res_register = client.post("/auth/register", json=user_data)
    assert res_register.status_code == 200
    assert "access_token" in res_register.json()

    # Test Connexion
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    res_login = client.post("/auth/login", json=login_data)

    assert res_login.status_code == 200
    assert "access_token" in res_login.json()

    mock_hash_password.assert_called_once_with(user_data["password"])
    mock_verify_password.assert_called_once_with(login_data["password"], "fake_hashed_password") # Vérifie l'appel avec le mot de passe du login

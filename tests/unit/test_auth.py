import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.mark.unit
@patch("app.database.get_connection")
@patch("app.security.password_handler.hash_password")
@patch("app.security.password_handler.verify_password")
def test_register_and_login(mock_verify_password, mock_hash_password, mock_get_connection):
    client = TestClient(app)

    # Mock de la connexion DB
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Logique pour simuler SELECT/INSERT
    def execute_side_effect(query, params=None):
        query = query.lower()
        if "insert into users" in query:
            mock_cursor.rowcount = 1
            mock_cursor.lastrowid = 1
        elif "select" in query and "from users" in query:
            mock_cursor.fetchone.return_value = {
                "id": 1,
                "username": "pytester",
                "email": "pytest@example.com",
                "password_hash": "fake_hashed_password"
            }
        else:
            mock_cursor.fetchone.return_value = None

    mock_cursor.execute.side_effect = execute_side_effect
    mock_hash_password.return_value = "fake_hashed_password"
    mock_verify_password.return_value = True

    user_data = {
        "username": "pytester",
        "email": "pytest@example.com",
        "password": "StrongPass123!"
    }

    # Register
    res = client.post("/auth/register", json=user_data)
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Login
    res = client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    mock_hash_password.assert_called_once_with(user_data["password"])
    mock_verify_password.assert_called_once_with(user_data["password"], "fake_hashed_password")

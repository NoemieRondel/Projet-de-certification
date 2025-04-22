import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@patch("app.reset_password_route.get_connection")
def test_reset_password_success(mock_get_connection):
    # Mock du curseur et de la connexion
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simuler un token valide non expiré
    mock_cursor.fetchone.return_value = {
        "user_id": 1,
        "expires_at": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }

    response = client.post(
        "/reset_password/fake-token",
        json={"new_password": "super_secure_pass123!"}
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Mot de passe réinitialisé avec succès"}

    # Vérifie que le mot de passe a été mis à jour et que le token est supprimé
    assert mock_cursor.execute.call_count >= 3


@patch("app.reset_password_route.get_connection")
def test_reset_password_invalid_token(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = None  # Token introuvable

    response = client.post("/reset_password/invalid-token", json={"new_password": "pass"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Token invalide ou expiré"


@patch("app.reset_password_route.get_connection")
def test_reset_password_expired_token(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = {
        "user_id": 1,
        "expires_at": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    }

    response = client.post("/reset_password/expired-token", json={"new_password": "pass"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Token expiré"

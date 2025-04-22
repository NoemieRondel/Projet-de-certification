import pytest
from fastapi.testclient import TestClient
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.main import app
from unittest.mock import patch

client = TestClient(app)


@pytest.fixture
def fake_email():
    return "testuser@example.com"


@patch("app.forgot_password_route.get_connection")
@patch("app.forgot_password_route.send_email")
def test_forgot_password_existing_user(mock_send_email, mock_get_connection, fake_email):
    # Simuler un utilisateur trouvé en base
    mock_cursor = mock_get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = {"id": 1}

    response = client.post("/forgot_password", json={"email": fake_email})

    assert response.status_code == 200
    assert "message" in response.json()
    assert "un lien de réinitialisation a été envoyé" in response.json()["message"]

    mock_send_email.assert_called_once()  # On vérifie que l'email a été "envoyé"


@patch("app.forgot_password_route.get_connection")
@patch("app.forgot_password_route.send_email")
def test_forgot_password_non_existing_user(mock_send_email, mock_get_connection, fake_email):
    # Simuler aucun utilisateur trouvé
    mock_cursor = mock_get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = None

    response = client.post("/forgot_password", json={"email": fake_email})

    assert response.status_code == 200
    assert "message" in response.json()
    assert "un lien de réinitialisation a été envoyé" in response.json()["message"]

    mock_send_email.assert_not_called()

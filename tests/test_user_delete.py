from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.main import app

client = TestClient(app)


@patch("app.user_delete_route.get_connection")
def test_delete_me_success(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_connection.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Simuler suppression réussie
    mock_cursor.rowcount = 1

    # Simuler un token d’auth avec user_id 1
    headers = {"Authorization": "Bearer fake-token"}

    with patch("app.user_delete_route.decode_jwt_token", return_value={"user_id": 1}):
        response = client.delete("/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"message": "Utilisateur supprimé avec succès"}

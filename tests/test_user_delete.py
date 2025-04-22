from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
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

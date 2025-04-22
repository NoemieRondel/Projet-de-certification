import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.mark.asyncio
@patch("app.routes.alerts.get_connection")
async def test_update_user_preferences_success(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    payload = {
        "source_preferences": "TechCrunch;The Verge",
        "video_channel_preferences": "DeepLearningAI",
        "keyword_preferences": "AI;ML;NLP"
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/preferences/1/filters", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Préférences de filtrage mises à jour avec succès."
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

@pytest.mark.asyncio
@patch("app.routes.alerts.get_connection")
async def test_update_user_preferences_db_error(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception("DB error")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    payload = {
        "source_preferences": "TechCrunch",
        "video_channel_preferences": "AI_Channels",
        "keyword_preferences": "GPT"
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/preferences/1/filters", json=payload)

    assert response.status_code == 500
    assert "Erreur interne" in response.json()["detail"]
    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
@patch("app.routes.alerts.get_connection", return_value=None)
async def test_update_user_preferences_connection_error(mock_get_connection):
    payload = {
        "source_preferences": "TechCrunch",
        "video_channel_preferences": "AI_Channels",
        "keyword_preferences": "GPT"
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/preferences/1/filters", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "Impossible de se connecter à la base de données."

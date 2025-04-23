import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)

VALID_TOKEN = "Bearer faketoken123"


class TestVideos:

    from app.main import app

    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection")
    def test_get_all_videos(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_get_connection.return_value = mock_conn

        mock_data = [{
            'id': 1,
            'title': 'AI Revolution',
            'video_url': 'https://example.com/video',
            'source': 'YouTube',
            'publication_date': datetime(2024, 11, 10).isoformat(),
            'description': 'A deep dive into AI.'
        }]

        mock_cursor.fetchall.return_value = mock_data

        response = self.client.get(
            "/videos/",
            headers={"Authorization": VALID_TOKEN},
            params={"start_date": "2024-01-01", "source": "YouTube"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == "AI Revolution"
        assert data[0]["publication_date"] == "2024-11-10T00:00:00"

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_get_video_sources(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_get_connection.return_value = mock_conn

        # Données de test retournées par fetchall
        mock_cursor.fetchall.return_value = [{"channel_name": "AI Channel"}, {"channel_name": "Tech Talks"}]

        response = self.client.get(
            "/videos/video-sources",
            headers={"Authorization": VALID_TOKEN}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "channel_name" in data[0]
        channel_names = [item["channel_name"] for item in data]
        assert "AI Channel" in channel_names
        assert "Tech Talks" in channel_names

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

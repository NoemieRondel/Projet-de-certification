import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

VALID_TOKEN = "Bearer faketoken123"


class TestDashboard:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        # Vérifier ce chemin de patch pour jwt_required
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
             yield

    @patch("app.database.get_connection")
    def test_get_dashboard_success(self, mock_get_connection):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None

        # Simuler les retours de base de données
        mock_cursor.fetchone.side_effect = [
            {"source_preferences": "TechCrunch;The Verge", "video_channel_preferences": "AI_Channel", "keyword_preferences": "AI;ML"},
            {"count": 2},
            {"count": 1},
            {"count": 1},
            {"count": 1},
        ]

        now = datetime.now()

        mock_cursor.fetchall.side_effect = [
            [
                {"id": 1, "title": "Article 1", "source": "TechCrunch", "link": "url", "publication_date": now.date(), "keywords": "AI;ML"}
            ],
            [
                {"id": 2, "title": "AI Article", "source": "TechCrunch", "link": "url", "publication_date": now.date(), "keywords": "AI"}
            ],
            [
                {"id": 1, "title": "Science Article", "abstract": "bla", "article_url": "url", "publication_date": now.date(), "keywords": "ML", "authors": "Author A"}
            ],
            [
                {"id": 1, "title": "AI Video", "source": "AI_Channel", "video_url": "video_url", "publication_date": now.date()}
            ],
            [
                {"keywords": "AI;ML", "publication_date": now.date()},
                {"keywords": "NLP", "publication_date": (now - timedelta(days=5)).date()},
            ],
        ]

        response = self.client.get("/dashboard/")

        assert response.status_code == 200
        data = response.json()

        assert "articles_by_source" in data
        assert isinstance(data["articles_by_source"], list)
        assert "articles_by_keywords" in data
        assert isinstance(data["articles_by_keywords"], list)
        assert "scientific_articles_by_keywords" in data
        assert isinstance(data["scientific_articles_by_keywords"], list)
        assert "latest_videos" in data
        assert isinstance(data["latest_videos"], list)
        assert "trending_keywords" in data
        assert isinstance(data["trending_keywords"], list)
        assert "metrics" in data
        assert isinstance(data["metrics"], dict)
        assert "trends_chart" in data
        assert isinstance(data["trends_chart"], dict)

        mock_get_connection.assert_called_once()
        mock_connection.cursor.assert_called_once()
        mock_cursor.fetchone.assert_called()
        mock_cursor.fetchall.assert_called()
        mock_connection.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_dashboard_missing_preferences(self, mock_get_connection):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_connection

        mock_cursor.fetchone.return_value = None

        response = self.client.get("/dashboard/")

        assert response.status_code == 404
        # Vérifier que le message d'erreur correspond exactement
        assert response.json()["detail"] == "No preferences found for user"

        mock_get_connection.assert_called_once()
        mock_connection.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchone.assert_called_once()
        mock_connection.close.assert_called_once()

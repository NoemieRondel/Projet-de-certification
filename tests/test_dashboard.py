import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestDashboard:

    from app.main import app

    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection")
    def test_get_dashboard_success(self, mock_get_connection):
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_connection

        # Résultats mockés
        mock_cursor.fetchone.side_effect = [
            {"source_preferences": "TechCrunch", "video_channel_preferences": "AI_Channel", "keyword_preferences": "AI;ML"},
            {"count": 2},  # articles_count pour les sources
            {"count": 1},  # articles_count pour les mots-clés
            {"count": 1},  # scientific_articles_count
            {"count": 1},  # videos_count
        ]

        now_str = datetime.now().isoformat()

        mock_cursor.fetchall.side_effect = [
            [  # articles_by_source
                {"id": 1, "title": "Article 1", "source": "TechCrunch", "link": "url", "publication_date": now_str, "keywords": "AI;ML"}
            ],
            [  # articles_by_keywords
                {"id": 2, "title": "AI Article", "source": "TechCrunch", "link": "url", "publication_date": now_str, "keywords": "AI"}
            ],
            [  # scientific_articles_by_keywords
                {"id": 1, "title": "Science Article", "abstract": "bla", "article_url": "url", "publication_date": now_str, "keywords": "ML", "authors": "Author A"}
            ],
            [  # latest_videos
                {"id": 1, "title": "AI Video", "source": "AI_Channel", "video_url": "video_url", "publication_date": now_str}
            ],
            [  # keyword evolution
                {"keywords": "AI;ML", "publication_date": now_str},
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
        assert "keyword_evolution" in data
        assert isinstance(data["keyword_evolution"], list)
        assert "metrics" in data
        assert isinstance(data["metrics"], dict)

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
        assert response.json()["detail"] == "No preferences found for user"

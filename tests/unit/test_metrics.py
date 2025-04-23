import os
import sys
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Ajout du chemin du projet pour que FastAPI trouve le module 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

VALID_TOKEN = "Bearer faketoken123"


class TestMetrics:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        # Vérifier ce chemin de patch pour jwt_required
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection")
    def test_get_articles_by_source(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        mock_data = [{"source": "TechCrunch", "count": 42}]
        mock_cursor.fetchall.return_value = mock_data

        # Vérifier le chemin de l'endpoint
        response = self.client.get("/metrics/articles-by-source", headers={"Authorization": VALID_TOKEN})

        assert response.status_code == 200
        assert response.json() == mock_data

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_get_videos_by_source(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        mock_data = [{"source": "YouTube", "count": 18}]
        mock_cursor.fetchall.return_value = mock_data

        # Vérifier le chemin de l'endpoint
        response = self.client.get("/metrics/videos-by-source", headers={"Authorization": VALID_TOKEN})

        assert response.status_code == 200
        assert response.json() == mock_data

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_get_keyword_frequency(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        mock_data = [{"keyword": "AI", "count": 10}]
        mock_cursor.fetchall.return_value = mock_data

        # Vérifier le chemin de l'endpoint
        response = self.client.get("/metrics/keyword-frequency", headers={"Authorization": VALID_TOKEN})

        assert response.status_code == 200
        assert response.json() == mock_data

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_get_scientific_keyword_frequency(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        mock_data = [{"keyword": "deep learning", "count": 7}]
        mock_cursor.fetchall.return_value = mock_data

        # Vérifier le chemin de l'endpoint
        response = self.client.get("/metrics/scientific-keyword-frequency", headers={"Authorization": VALID_TOKEN})

        assert response.status_code == 200
        assert response.json() == mock_data

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.get_connection")
    def test_get_monitoring_logs(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        # Simuler la date et la convertir en string
        now = datetime.utcnow()
        now_str = now.isoformat()

        mock_data = [{
            "timestamp": now,
            "script": "collect_articles.py",
            "duration_seconds": 4.5,
            "articles_count": 100,
            "empty_full_content_count": 2,
            "average_keywords_per_article": 5.3,
            "scientific_articles_count": 30,
            "empty_abstracts_count": 1,
            "average_keywords_per_scientific_article": 4.1,
            "summaries_generated": 25,
            "average_summary_word_count": 80.0
        }]

        mock_cursor.fetchall.return_value = mock_data

        # Vérifier le chemin de l'endpoint
        response = self.client.get("/metrics/monitoring-logs", headers={"Authorization": VALID_TOKEN})

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        # Vérifier que le timestamp est bien converti en string dans JSON
        assert response.json()[0]["timestamp"] == now_str

        mock_get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

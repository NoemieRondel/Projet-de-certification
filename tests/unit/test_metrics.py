import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.security.jwt_handler import jwt_required
from app.main import app


class TestMetrics:
    client = TestClient(app)

    @pytest.fixture(autouse=True, scope="class")
    def setup_class_auth_override(self):
        class MockUser:
            id = 1
            username = "testuser"
            email = "test@example.com"

        def mock_get_current_user_func():
            return {"user_id": 1}

        # Use the correct dependency (jwt_required) for the override
        original_override = self.app.dependency_overrides.get(jwt_required)
        self.app.dependency_overrides[jwt_required] = mock_get_current_user_func

        yield

        if original_override:
            self.app.dependency_overrides[jwt_required] = original_override
        else:
            del self.app.dependency_overrides[jwt_required]

    @patch("app.database.connection_pool")
    def test_get_articles_by_source(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_pool.get_connection.return_value = mock_conn

        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_data = [{"source": "TechCrunch", "count": 42}]
        mock_cursor.fetchall.return_value = mock_data

        response = self.client.get("/metrics/articles-by-source")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == mock_data, f"Expected {mock_data}, got {response.json()}. Response: {response.text}"

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_get_videos_by_source(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_data = [{"source": "YouTube", "count": 18}]
        mock_cursor.fetchall.return_value = mock_data

        response = self.client.get("/metrics/videos-by-source")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == mock_data, f"Expected {mock_data}, got {response.json()}. Response: {response.text}"

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_get_keyword_frequency(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_data = [{"keyword": "AI", "count": 10}]
        mock_cursor.fetchall.return_value = mock_data

        response = self.client.get("/metrics/keyword-frequency")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == mock_data, f"Expected {mock_data}, got {response.json()}. Response: {response.text}"

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_get_scientific_keyword_frequency(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

        mock_data = [{"keyword": "deep learning", "count": 7}]
        mock_cursor.fetchall.return_value = mock_data

        response = self.client.get("/metrics/scientific-keyword-frequency")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert response.json() == mock_data, f"Expected {mock_data}, got {response.json()}. Response: {response.text}"

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.connection_pool")
    def test_get_monitoring_logs(self, mock_pool):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pool.get_connection.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_conn.close.return_value = None

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

        response = self.client.get("/metrics/monitoring-logs")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        assert data[0]["timestamp"] == now_str

        mock_pool.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_conn.close.assert_called_once()

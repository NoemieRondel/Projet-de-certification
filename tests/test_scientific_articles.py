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

VALID_TOKEN = "Bearer faketoken123"


class TestScientificArticles:

    from app.main import app

    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection")
    def test_get_all_scientific_articles(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        # Résultats mockés
        mock_cursor.fetchall.return_value = [{
            'id': 1,
            'title': 'AI in Healthcare',
            'article_url': 'https://example.com/article',
            'authors': 'John Doe',
            'publication_date': '2024-10-01',
            'keywords': 'AI, Health',
            'abstract': 'This article discusses AI in healthcare.'
        }]

        response = self.client.get(
            "/scientific_articles/",
            headers={"Authorization": VALID_TOKEN}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == "AI in Healthcare"

    @patch("app.database.get_connection")
    def test_get_latest_scientific_articles(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_get_connection.return_value = mock_conn

        # Résultats mockés
        mock_cursor.fetchall.return_value = [{
            'id': 2,
            'title': 'Latest Advances in NLP',
            'article_url': 'https://example.com/nlp',
            'authors': 'Jane Smith',
            'publication_date': '2024-11-15',
            'keywords': 'NLP, Transformers',
            'abstract': 'Explores latest trends in NLP.'
        }]

        response = self.client.get(
            "/scientific_articles/latest",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["title"] == "Latest Advances in NLP"

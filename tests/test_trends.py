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


class TestTrends:
    from app.main import app
    client = TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        # Vérifier ce chemin de patch pour jwt_required
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.execute_query")
    def test_get_trending_keywords(self, mock_execute_query):
        fake_keywords = [
            {"keyword": "AI", "count": 15},
            {"keyword": "machine learning", "count": 10},
            {"keyword": "NLP", "count": 5}
        ]

        mock_execute_query.return_value = fake_keywords

        # Vérifier le chemin de l'endpoint
        response = self.client.get(
            "/trends/keywords",
            headers={"Authorization": VALID_TOKEN},
            params={"last_days": 30, "limit": 10, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert "trending_keywords" in data
        assert isinstance(data["trending_keywords"], list)
        assert len(data["trending_keywords"]) > 0
        assert data["trending_keywords"][0]["keyword"] == "AI"

        mock_execute_query.assert_called_once()

    def test_get_trending_keywords_invalid_dates(self):
        # Vérifier le chemin de l'endpoint
        response = self.client.get(
            "/trends/keywords",
            headers={"Authorization": VALID_TOKEN},
            params={"start_date": "2025-01-01", "end_date": "2024-01-01"}
        )

        assert response.status_code == 400
        # Vérifier le message d'erreur exact
        assert response.json()["detail"] == "La date de début doit être antérieure à la date de fin."

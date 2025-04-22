import pytest
from httpx import AsyncClient
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

# ==============================================================================
# IMPORTANT : Simuler l'initialisation du pool de connexion AVANT d'importer app.main


@patch('mysql.connector.pooling.MySQLConnectionPool')
class TestTrends:
# ==============================================================================

    from app.main import app

    @pytest.fixture(autouse=True)
    def mock_auth_dependency(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}) as mock:
            yield mock

    @pytest.mark.asyncio
    @patch("app.database.execute_query")
    async def test_get_trending_keywords(self, mock_execute_query):
        fake_keywords = [
            {"keyword": "AI", "count": 15},
            {"keyword": "machine learning", "count": 10},
            {"keyword": "NLP", "count": 5}
        ]

        mock_execute_query.return_value = fake_keywords

        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get(
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

    @pytest.mark.asyncio
    @patch("app.database.execute_query")
    async def test_get_trending_keywords_invalid_dates(self, mock_execute_query):
        mock_execute_query.return_value = []

        async with AsyncClient(app=self.app, base_url="http://test") as ac:
            response = await ac.get(
                "/trends/keywords",
                headers={"Authorization": VALID_TOKEN},
                params={"start_date": "2025-01-01", "end_date": "2024-01-01"}
            )

        assert response.status_code == 400
        assert "La date de début doit être antérieure à la date de fin." in response.text

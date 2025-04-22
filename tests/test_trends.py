import pytest
from httpx import AsyncClient
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.main import app
from datetime import datetime, timedelta

VALID_TOKEN = "Bearer faketoken123"


@pytest.mark.asyncio
async def test_get_trending_keywords(monkeypatch):
    fake_keywords = [
        {"keyword": "AI", "count": 15},
        {"keyword": "machine learning", "count": 10},
        {"keyword": "NLP", "count": 5}
    ]

    async def mock_execute_query(query, params):
        return fake_keywords

    monkeypatch.setattr("app.routes.trends.execute_query", mock_execute_query)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/trends/keywords",
            headers={"Authorization": VALID_TOKEN},
            params={"last_days": 30, "limit": 10, "offset": 0}
        )

    assert response.status_code == 200
    data = response.json()
    assert "trending_keywords" in data
    assert isinstance(data["trending_keywords"], list)
    assert data["trending_keywords"][0]["keyword"] == "AI"


@pytest.mark.asyncio
async def test_get_trending_keywords_invalid_dates(monkeypatch):
    async def dummy_execute_query(query, params):
        return []

    monkeypatch.setattr("app.routes.trends.execute_query", dummy_execute_query)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Intentionally sending invalid date range
        response = await ac.get(
            "/trends/keywords",
            headers={"Authorization": VALID_TOKEN},
            params={"start_date": "2025-01-01", "end_date": "2024-01-01"}
        )

    assert response.status_code == 400
    assert "La date de début doit être antérieure à la date de fin." in response.text

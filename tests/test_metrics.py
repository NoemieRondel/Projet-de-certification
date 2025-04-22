import pytest
from httpx import AsyncClient
from app.main import app
from datetime import datetime

VALID_TOKEN = "Bearer faketoken123"


@pytest.mark.asyncio
async def test_get_articles_by_source(monkeypatch):
    mock_data = [{"source": "TechCrunch", "count": 42}]
    monkeypatch.setattr("app.routes.metrics.execute_query", lambda q, params=(): mock_data)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/articles-by-source", headers={"Authorization": VALID_TOKEN})
    assert response.status_code == 200
    assert response.json() == mock_data


@pytest.mark.asyncio
async def test_get_videos_by_source(monkeypatch):
    mock_data = [{"source": "YouTube", "count": 18}]
    monkeypatch.setattr("app.routes.metrics.execute_query", lambda q, params=(): mock_data)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/videos-by-source", headers={"Authorization": VALID_TOKEN})
    assert response.status_code == 200
    assert response.json() == mock_data


@pytest.mark.asyncio
async def test_get_keyword_frequency(monkeypatch):
    mock_data = [{"keyword": "AI", "count": 10}]
    monkeypatch.setattr("app.routes.metrics.execute_query", lambda q, params=(): mock_data)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/keyword-frequency", headers={"Authorization": VALID_TOKEN})
    assert response.status_code == 200
    assert response.json() == mock_data


@pytest.mark.asyncio
async def test_get_scientific_keyword_frequency(monkeypatch):
    mock_data = [{"keyword": "deep learning", "count": 7}]
    monkeypatch.setattr("app.routes.metrics.execute_query", lambda q, params=(): mock_data)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/scientific-keyword-frequency", headers={"Authorization": VALID_TOKEN})
    assert response.status_code == 200
    assert response.json() == mock_data


@pytest.mark.asyncio
async def test_get_monitoring_logs(monkeypatch):
    now = datetime.utcnow().isoformat()
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

    monkeypatch.setattr("app.routes.metrics.execute_query", lambda q, params=(): mock_data)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/monitoring-logs", headers={"Authorization": VALID_TOKEN})

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["script"] == "collect_articles.py"

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

# Token JWT factice pour les tests
VALID_TOKEN = "Bearer faketoken123"


@pytest.mark.asyncio
async def test_get_all_scientific_articles(monkeypatch):
    async def mock_get_connection():
        class FakeCursor:
            def execute(self, query, params):
                self.results = [{
                    'id': 1,
                    'title': 'AI in Healthcare',
                    'article_url': 'https://example.com/article',
                    'authors': 'John Doe',
                    'publication_date': '2024-10-01',
                    'keywords': 'AI, Health',
                    'abstract': 'This article discusses AI in healthcare.'
                }]

            def fetchall(self): return self.results
            def close(self): pass

        class FakeConnection:
            def cursor(self, dictionary=True): return FakeCursor()
            def close(self): pass
        return FakeConnection()

    monkeypatch.setattr("app.routes.scientific_articles.get_connection", mock_get_connection)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/scientific_articles/",
            headers={"Authorization": VALID_TOKEN}
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "AI in Healthcare"


@pytest.mark.asyncio
async def test_get_latest_scientific_articles(monkeypatch):
    async def mock_get_connection():
        class FakeCursor:
            def execute(self, query):
                self.results = [{
                    'id': 2,
                    'title': 'Latest Advances in NLP',
                    'article_url': 'https://example.com/nlp',
                    'authors': 'Jane Smith',
                    'publication_date': '2024-11-15',
                    'keywords': 'NLP, Transformers',
                    'abstract': 'Explores latest trends in NLP.'
                }]

            def fetchall(self): return self.results
            def close(self): pass

        class FakeConnection:
            def cursor(self, dictionary=True): return FakeCursor()
            def close(self): pass
        return FakeConnection()

    monkeypatch.setattr("app.routes.scientific_articles.get_connection", mock_get_connection)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/scientific_articles/latest",
            headers={"Authorization": VALID_TOKEN}
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "Latest Advances in NLP"

import pytest
from httpx import AsyncClient
from app.main import app
from datetime import datetime

VALID_TOKEN = "Bearer faketoken123"


@pytest.mark.asyncio
async def test_get_all_videos(monkeypatch):
    async def mock_get_connection():
        class FakeCursor:
            def execute(self, query, params):
                self.results = [{
                    'id': 1,
                    'title': 'AI Revolution',
                    'video_url': 'https://example.com/video',
                    'source': 'YouTube',
                    'publication_date': datetime(2024, 11, 10),
                    'description': 'A deep dive into AI.'
                }]

            def fetchall(self): return self.results
            def close(self): pass

        class FakeConnection:
            def cursor(self, dictionary=True): return FakeCursor()
            def close(self): pass
        return FakeConnection()

    monkeypatch.setattr("app.routes.videos.get_connection", mock_get_connection)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/videos/",
            headers={"Authorization": VALID_TOKEN},
            params={"start_date": "2024-01-01", "source": "YouTube"}
        )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["title"] == "AI Revolution"
    assert data[0]["publication_date"] == "2024-11-10"


@pytest.mark.asyncio
async def test_get_video_sources(monkeypatch):
    async def mock_get_connection():
        class FakeCursor:
            def execute(self, query):
                self.results = [{"channel_name": "AI Channel"}, {"channel_name": "Tech Talks"}]

            def fetchall(self): return self.results
            def close(self): pass

        class FakeConnection:
            def cursor(self, dictionary=True): return FakeCursor()
            def close(self): pass
        return FakeConnection()

    monkeypatch.setattr("app.routes.videos.get_connection", mock_get_connection)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/videos/video-sources",
            headers={"Authorization": VALID_TOKEN}
        )
    assert response.status_code == 200
    data = response.json()
    assert "channel_name" in data
    assert "AI Channel" in data["channel_name"]
    assert "Tech Talks" in data["channel_name"]

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app
from datetime import datetime


@pytest.mark.asyncio
@patch("app.routes.dashboard.get_connection")
@patch("app.routes.dashboard.jwt_required")
async def test_get_dashboard_success(mock_jwt_required, mock_get_connection):
    # Simule un utilisateur authentifié
    mock_jwt_required.return_value = {"user_id": 1}

    # Mock de la connexion MySQL et du curseur
    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_connection

    # Résultats mockés
    mock_cursor.fetchone.side_effect = [
        {"source_preferences": "TechCrunch", "video_channel_preferences": "AI_Channel", "keyword_preferences": "AI;ML"},
        {"count": 2},  # articles_count for sources
        {"count": 1},  # articles_count for keywords
        {"count": 1},  # scientific_articles_count
        {"count": 1},  # videos_count
    ]

    mock_cursor.fetchall.side_effect = [
        [  # articles_by_source
            {"id": 1, "title": "Article 1", "source": "TechCrunch", "link": "url", "publication_date": datetime.now(), "keywords": "AI;ML"}
        ],
        [  # articles_by_keywords
            {"id": 2, "title": "AI Article", "source": "TechCrunch", "link": "url", "publication_date": datetime.now(), "keywords": "AI"}
        ],
        [  # scientific_articles_by_keywords
            {"id": 1, "title": "Science Article", "abstract": "bla", "article_url": "url", "publication_date": datetime.now(), "keywords": "ML", "authors": "Author A"}
        ],
        [  # latest_videos
            {"id": 1, "title": "AI Video", "source": "AI_Channel", "video_url": "video_url", "publication_date": datetime.now()}
        ],
        [  # keyword evolution
            {"keywords": "AI;ML", "publication_date": datetime.now()},
        ],
    ]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/dashboard/")

    assert response.status_code == 200
    data = response.json()
    assert "articles_by_source" in data
    assert "trending_keywords" in data
    assert "metrics" in data


@pytest.mark.asyncio
@patch("app.routes.dashboard.get_connection")
@patch("app.routes.dashboard.jwt_required")
async def test_dashboard_missing_preferences(mock_jwt_required, mock_get_connection):
    mock_jwt_required.return_value = {"user_id": 1}

    mock_cursor = MagicMock()
    mock_connection = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_connection

    # Cette fois, aucune préférence utilisateur n’est renvoyée
    mock_cursor.fetchone.return_value = None

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/dashboard/")

    assert response.status_code == 404
    assert response.json()["detail"] == "No preferences found for user"

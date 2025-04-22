import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_jwt():
    with patch("app.articles_route.jwt_required", return_value={"user_id": 1}):
        yield


@patch("app.articles_route.get_connection")
def test_get_all_articles_without_filters(mock_get_connection, mock_jwt):
    # Mock de la base
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "title": "Article 1",
            "source": "TechCrunch",
            "publication_date": "2024-10-10",
            "keywords": "AI;ML",
            "summary": "Résumé...",
            "link": "https://example.com/article1"
        }
    ]

    with patch("app.articles_route.jwt_required", return_value={"user_id": 1}):
        response = client.get("/articles/")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Article 1"
    assert response.json()[0]["source"] == "TechCrunch"


@patch("app.articles_route.get_connection")
def test_get_all_articles_with_filters(mock_get_connection, mock_jwt):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        {
            "id": 2,
            "title": "Filtered Article",
            "source": "Wired",
            "publication_date": "2024-12-01",
            "keywords": "AI;NLP",
            "summary": "Résumé filtré...",
            "link": "https://example.com/article2"
        }
    ]

    with patch("app.articles_route.jwt_required", return_value={"user_id": 1}):
        response = client.get("/articles/?source=Wired&keywords=AI")

    assert response.status_code == 200
    assert response.json()[0]["source"] == "Wired"


@patch("app.articles_route.get_connection")
def test_get_all_articles_not_found(mock_get_connection, mock_jwt):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    mock_cursor.fetchall.return_value = []

    with patch("app.articles_route.jwt_required", return_value={"user_id": 1}):
        response = client.get("/articles/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Aucun article trouvé."


@patch("app.articles_route.get_connection")
def test_get_latest_articles(mock_get_connection, mock_jwt):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        {
            "id": 3,
            "title": "Dernier article",
            "source": "TechCrunch",
            "publication_date": "2024-12-31",
            "keywords": "RAG",
            "summary": "Le dernier article...",
            "link": "https://example.com/article3"
        }
    ]

    with patch("app.articles_route.jwt_required", return_value={"user_id": 1}):
        response = client.get("/articles/latest")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Dernier article"
    assert response.json()[0]["source"] == "TechCrunch"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Ajout du chemin du projet à sys.path pour que l'importation fonctionne correctement
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app  # Import de l'application FastAPI depuis app.main


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# Fonction pour obtenir un token JWT fictif (simulé pour les tests)
def get_fake_jwt_token():
    return "fake-jwt-token"


# Test pour /articles-by-source
def test_get_articles_by_source(client):
    mock_data = [
        {"source": "TechCrunch", "count": 100},
        {"source": "VentureBeat", "count": 80},
    ]

    headers = {"Authorization": f"Bearer {get_fake_jwt_token()}"}

    with patch("app.routes.metrics.execute_query", return_value=mock_data):
        response = client.get("/articles-by-source", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["source"] == "TechCrunch"
    assert response_data[0]["count"] == 100
    assert response_data[1]["source"] == "VentureBeat"
    assert response_data[1]["count"] == 80


# Test pour /keyword-frequency
def test_get_keyword_frequency(client):
    mock_data = [
        {"keyword": "AI", "count": 150},
        {"keyword": "Machine Learning", "count": 120},
    ]

    headers = {"Authorization": f"Bearer {get_fake_jwt_token()}"}

    with patch("app.routes.metrics.execute_query", return_value=mock_data):
        response = client.get("/keyword-frequency", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["keyword"] == "AI"
    assert response_data[0]["count"] == 150
    assert response_data[1]["keyword"] == "Machine Learning"
    assert response_data[1]["count"] == 120


# Test pour /scientific-keyword-frequency
def test_get_scientific_keyword_frequency(client):
    mock_data = [
        {"keyword": "Deep Learning", "count": 50},
        {"keyword": "Neural Networks", "count": 40},
    ]

    headers = {"Authorization": f"Bearer {get_fake_jwt_token()}"}

    with patch("app.routes.metrics.execute_query", return_value=mock_data):
        response = client.get("/scientific-keyword-frequency", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["keyword"] == "Deep Learning"
    assert response_data[0]["count"] == 50
    assert response_data[1]["keyword"] == "Neural Networks"
    assert response_data[1]["count"] == 40


# Test pour /videos-by-source
def test_get_videos_by_source(client):
    mock_data = [
        {"source": "YouTube", "count": 200},
        {"source": "Vimeo", "count": 150},
    ]

    headers = {"Authorization": f"Bearer {get_fake_jwt_token()}"}

    with patch("app.routes.metrics.execute_query", return_value=mock_data):
        response = client.get("/videos-by-source", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["source"] == "YouTube"
    assert response_data[0]["count"] == 200
    assert response_data[1]["source"] == "Vimeo"
    assert response_data[1]["count"] == 150


# Test pour /monitoring-logs
def test_get_monitoring_logs(client):
    mock_data = [
        {
            "timestamp": "2025-04-24T10:00:00",
            "script": "article_scraper",
            "duration_seconds": 120.5,
            "articles_count": 100,
            "empty_full_content_count": 5,
            "average_keywords_per_article": 3.5,
            "scientific_articles_count": 20,
            "empty_abstracts_count": 2,
            "average_keywords_per_scientific_article": 4.0,
            "summaries_generated": 15,
            "average_summary_word_count": 200.0
        },
        {
            "timestamp": "2025-04-24T11:00:00",
            "script": "video_scraper",
            "duration_seconds": 60.2,
            "articles_count": 50,
            "empty_full_content_count": 3,
            "average_keywords_per_article": 2.8,
            "scientific_articles_count": 10,
            "empty_abstracts_count": 1,
            "average_keywords_per_scientific_article": 3.2,
            "summaries_generated": 8,
            "average_summary_word_count": 180.0
        },
    ]

    headers = {"Authorization": f"Bearer {get_fake_jwt_token()}"}

    with patch("app.routes.metrics.execute_query", return_value=mock_data):
        response = client.get("/monitoring-logs", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["timestamp"] == "2025-04-24T10:00:00"
    assert response_data[0]["script"] == "article_scraper"
    assert response_data[0]["duration_seconds"] == 120.5
    assert response_data[0]["articles_count"] == 100
    assert response_data[0]["empty_full_content_count"] == 5
    assert response_data[0]["average_keywords_per_article"] == 3.5
    assert response_data[0]["scientific_articles_count"] == 20
    assert response_data[0]["empty_abstracts_count"] == 2
    assert response_data[0]["average_keywords_per_scientific_article"] == 4.0
    assert response_data[0]["summaries_generated"] == 15
    assert response_data[0]["average_summary_word_count"] == 200.0
    assert response_data[1]["timestamp"] == "2025-04-24T11:00:00"
    assert response_data[1]["script"] == "video_scraper"
    assert response_data[1]["duration_seconds"] == 60.2
    assert response_data[1]["articles_count"] == 50
    assert response_data[1]["empty_full_content_count"] == 3
    assert response_data[1]["average_keywords_per_article"] == 2.8
    assert response_data[1]["scientific_articles_count"] == 10
    assert response_data[1]["empty_abstracts_count"] == 1
    assert response_data[1]["average_keywords_per_scientific_article"] == 3.2
    assert response_data[1]["summaries_generated"] == 8
    assert response_data[1]["average_summary_word_count"] == 180.0

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ==============================================================================
# IMPORTANT : Simuler l'initialisation du pool de connexion avant d'importer app.main

@patch('mysql.connector.pooling.MySQLConnectionPool')
class TestArticles:

#==============================================================================

    from app.main import app
    client = TestClient(app)

    # Fixture pour simuler jwt_required
    @pytest.fixture(autouse=True)
    def mock_jwt(self):
        with patch("app.security.jwt_handler.jwt_required", return_value={"user_id": 1}):
            yield

    @patch("app.database.get_connection") # Simule get_connection
    def test_get_all_articles_without_filters(self, mock_get_connection):
        # Mock de la base
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_get_connection.return_value = mock_conn

        # Données de test retournées par fetchall
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

        # Exécutez la requête via le client de test
        response = self.client.get("/articles/")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Article 1"
        assert data[0]["source"] == "TechCrunch"

    @patch("app.database.get_connection") # Simulatez get_connection
    def test_get_all_articles_with_filters(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

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

        response = self.client.get("/articles/?source=Wired&keywords=AI")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["source"] == "Wired"

    @patch("app.database.get_connection")
    def test_get_all_articles_not_found(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

        mock_get_connection.return_value = mock_conn

        mock_cursor.fetchall.return_value = []

        response = self.client.get("/articles/")

        assert response.status_code == 404
        assert response.json()["detail"] == "Aucun article trouvé."

    @patch("app.database.get_connection")
    def test_get_latest_articles(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None

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

        response = self.client.get("/articles/latest")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Dernier article"
        assert data[0]["source"] == "TechCrunch"

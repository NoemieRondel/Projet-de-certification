import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Ajout du chemin du projet à sys.path pour que l'importation fonctionne correctement
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app


# Fonction pour obtenir la connexion à la base de données
def get_connection():
    import mysql.connector
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="test_db"
    )


@pytest.fixture(scope="module")
def setup_database():
    # Code pour réinitialiser la base de données avant les tests
    connection = get_connection()
    schema_path = os.path.join(project_root, "schema.sql")
    with open(schema_path, "r") as f:
        schema = f.read()
    cursor = connection.cursor()
    cursor.execute(schema)  # Exécuter le schema.sql pour créer les tables et insérer les données
    connection.commit()

    yield

    # Code pour nettoyer la base de données après les tests
    cursor.execute("DROP DATABASE IF EXISTS test_db")
    connection.commit()


def test_register_user(setup_database):
    client = TestClient(app)
    response = client.post(
        "/register",
        json={"username": "newuser", "email": "newuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_user_existing_email(setup_database):
    client = TestClient(app)
    response = client.post(
        "/register",
        json={"username": "newuser", "email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email déjà utilisé."


def test_login_user(setup_database):
    client = TestClient(app)
    response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_user_invalid_credentials(setup_database):
    client = TestClient(app)
    response = client.post(
        "/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiants invalides."

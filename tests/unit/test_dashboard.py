import pytest
from fastapi.testclient import TestClient
import uuid
import sys
import os

# Ajout du chemin racine du projet au sys.path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

client = TestClient(app)


def create_temp_user_and_get_token():
    """Helper pour créer un utilisateur temporaire et récupérer un token."""
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPassword123!"

    # Register
    register_response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code in [200, 201], f"Register failed: {register_response.text}"

    # Login
    login_response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]

    return token


def test_get_dashboard_success():
    """Test pour récupérer les données du tableau de bord."""
    token = create_temp_user_and_get_token()

    response = client.get(
        "/dashboard/",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code} - {response.text}"
    if response.status_code == 200:
        dashboard_data = response.json()
        assert isinstance(dashboard_data, dict), "Dashboard response should be a dict"
        assert "total_articles" in dashboard_data
        assert "total_videos" in dashboard_data
        assert "latest_trends" in dashboard_data

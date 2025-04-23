import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

client = TestClient(app)

class TestEndToEndFlow:

    def test_register_login_and_access_protected_route(self):
        # Générer un email unique à chaque test
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"

        # Étape 1 : inscription
        register_payload = {
            "email": unique_email,
            "password": password
        }

        register_response = client.post("/auth/register", json=register_payload)
        assert register_response.status_code in [200, 201]

        # Étape 2 : login
        login_payload = {
            "email": unique_email,
            "password": password
        }

        login_response = client.post("/auth/login", data=login_payload)
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "access_token" in token_data

        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Étape 3 : accéder à une route protégée
        response = client.get("/articles/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

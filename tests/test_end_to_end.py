import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid

current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

client = TestClient(app)


class TestEndToEndFlow:

    def test_register_login_and_access_protected_route(self):
        unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        unique_username = f"testuser_{uuid.uuid4().hex[:4]}"

        register_payload = {
            "username": unique_username,
            "email": unique_email,
            "password": password
        }

        register_response = client.post("/auth/register", json=register_payload)
        assert register_response.status_code in [200, 201]

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

        response = client.get("/articles/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
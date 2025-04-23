import pytest
from fastapi.testclient import TestClient
import sys
import os
import uuid


current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app


class TestArticles:
    client = TestClient(app)

    @pytest.fixture(scope="class")
    def auth_headers(self):
        unique_email = f"test_art_int_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        unique_username = f"test_art_int_{uuid.uuid4().hex[:4]}"

        register_payload = {
            "username": unique_username,
            "email": unique_email,
            "password": password
        }
        reg_resp = self.client.post("/auth/register", json=register_payload)
        assert reg_resp.status_code in [200, 201], f"Registration failed in auth_headers fixture: {reg_resp.status_code}, {reg_resp.text}"

        login_payload = {
            "email": unique_email,
            "password": password
        }

        login_resp = self.client.post("/auth/login", json=login_payload)
        assert login_resp.status_code == 200, f"Login failed in auth_headers fixture: {login_resp.status_code}. Response detail: {login_resp.text}"

        token_data = login_resp.json()
        assert "access_token" in token_data, f"Login response missing access_token. Response: {token_data}"
        token = token_data["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        yield headers

    def test_get_all_articles_without_filters(self, auth_headers):
        response = self.client.get("/articles/", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_articles_with_filters(self, auth_headers):
        response = self.client.get("/articles/?source=Wired&keywords=AI", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert isinstance(data, list)

    def test_get_all_articles_not_found(self, auth_headers):
        response = self.client.get("/articles/", headers=auth_headers)

        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}. Response: {response.text}"
        if response.status_code == 404:
            assert response.json()["detail"] == "Aucun article trouvé."

    def test_get_latest_articles(self, auth_headers):
        response = self.client.get("/articles/latest", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert isinstance(data, list)
import pytest
from fastapi.testclient import TestClient
import sys
import os
from datetime import datetime, timedelta
import uuid


current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from app.main import app


class TestVideos:
    client = TestClient(app)

    @pytest.fixture(scope="class")
    def auth_headers(self):
        unique_email = f"test_vid_int_{uuid.uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"
        unique_username = f"test_vid_int_{uuid.uuid4().hex[:4]}"

        register_payload = {
            "username": unique_username,
            "email": unique_email,
            "password": password
        }
        reg_resp = self.client.post("/auth/register", json=register_payload)
        assert reg_resp.status_code in [200, 201], f"Registration failed in auth_headers fixture: {reg_resp.status_code}, {reg_resp.text}"

        login_payload = {
            "username": unique_username,
            "password": password
        }
        login_resp = self.client.post("/auth/login", data=login_payload)
        assert login_resp.status_code == 200, f"Login failed in auth_headers fixture: {login_resp.status_code}, {login_resp.text}"

        token_data = login_resp.json()
        assert "access_token" in token_data, f"Login response missing access_token in auth_headers fixture: {token_data}"
        token = token_data["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        yield headers

    def test_get_all_videos(self, auth_headers):
        response = self.client.get(
            "/videos/",
            headers=auth_headers,
            params={"start_date": "2024-01-01", "source": "YouTube"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # assert len(data) >= 0 # Adaptez si besoin
        # if data:
        #     assert data[0]["title"]
        #     assert data[0]["publication_date"]

    def test_get_video_sources(self, auth_headers):
        response = self.client.get(
            "/videos/video-sources",
            headers=auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        data = response.json()

        assert isinstance(data, dict)
        assert "channel_name" in data
        assert isinstance(data["channel_name"], list)
        assert len(data["channel_name"]) > 0

        channel_names = data["channel_name"]

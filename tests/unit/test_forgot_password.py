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


def create_temp_user():
    """Helper pour créer un utilisateur temporaire pour le test de forgot_password."""
    email = f"forgot_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "ForgotPasswordTest123!"

    # Register
    register_response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert register_response.status_code in [200, 201], f"Register failed: {register_response.text}"

    return email


def test_forgot_password_existing_email():
    """Test de la route forgot_password avec un email existant."""
    email = create_temp_user()

    response = client.post("/auth/forgot_password", json={"email": email})

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert response.json() == {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}


def test_forgot_password_non_existing_email():
    """Test de la route forgot_password avec un email inexistant."""
    fake_email = f"fake_{uuid.uuid4().hex[:6]}@example.com"

    response = client.post("/auth/forgot_password", json={"email": fake_email})

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert response.json() == {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}

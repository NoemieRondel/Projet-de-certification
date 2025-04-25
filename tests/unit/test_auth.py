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


def test_register_user_success():
    """Test de l'inscription d'un utilisateur avec des informations uniques."""
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPassword123!"

    response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    assert response.status_code in [200, 201], f"Register failed: {response.text}"


def test_register_user_email_exists():
    """Test de l'inscription avec un email déjà existant."""
    # On commence par créer un utilisateur
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPassword123!"

    # Création d'un premier utilisateur
    response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code in [200, 201], f"Initial register failed: {response.text}"

    # On tente de s'inscrire à nouveau avec le même email
    response = client.post("/auth/register", json={
        "username": "anotheruser",
        "email": email,  # même email
        "password": "NewPassword123!"
    })

    assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.text}"


def test_login_user_success():
    """Test du login avec des identifiants corrects."""
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "TestPassword123!"

    # Inscription de l'utilisateur
    response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert response.status_code in [200, 201], f"Register failed: {response.text}"

    # Login avec les mêmes informations
    login_response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })

    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token_data = login_response.json()
    assert "access_token" in token_data, "Access token missing in login response"


def test_login_user_invalid_credentials():
    """Test du login avec des identifiants incorrects."""
    email = f"testuser_{uuid.uuid4().hex[:6]}@example.com"
    password = "TestPassword123!"

    # Tentative de login avec un mauvais mot de passe
    login_response = client.post("/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })

    assert login_response.status_code == 401, f"Expected 401 for wrong password, got {login_response.status_code}"


def test_login_user_not_found():
    """Test du login avec un email non existant."""
    login_response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "TestPassword123!"
    })

    assert login_response.status_code == 401, f"Expected 401 for non-existent user, got {login_response.status_code}"

import pytest
from fastapi.testclient import TestClient
import uuid
import sys
import os
import datetime
import mysql.connector
import bcrypt

# Ajout du chemin racine du projet au sys.path
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app
from app.database import get_connection

client = TestClient(app)


def create_temp_user():
    """Helper pour créer un utilisateur temporaire directement en base."""
    email = f"resetuser_{uuid.uuid4().hex[:6]}@example.com"
    username = f"user_{uuid.uuid4().hex[:6]}"
    password = "ResetPassword123!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid

    return user_id, email, password


def create_reset_token_for_user(user_id):
    """Helper pour créer un token de reset pour un utilisateur."""
    token = uuid.uuid4().hex
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user_id, token, expires_at)
        )
        conn.commit()

    return token


def get_user_password_hash(user_id):
    """Helper pour récupérer le hash du mot de passe d'un utilisateur."""
    with get_connection() as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = %s", (user_id,)
        )
        result = cursor.fetchone()
    return result["password_hash"] if result else None


def test_reset_password_success():
    """Test POST /auth/reset_password/{token} avec succès."""
    user_id, email, old_password = create_temp_user()
    token = create_reset_token_for_user(user_id)

    new_password = "NewSecurePassword456!"

    response = client.post(
        f"/auth/reset_password/{token}",
        json={"new_password": new_password}
    )

    assert response.status_code == 200, f"Unexpected status code: {response.status_code} - {response.text}"
    assert response.json() == {"message": "Mot de passe réinitialisé avec succès"}

    # Vérifier que le mot de passe a changé
    new_password_hash = get_user_password_hash(user_id)
    assert bcrypt.checkpw(new_password.encode('utf-8'), new_password_hash.encode('utf-8'))


def test_reset_password_invalid_token():
    """Test POST /auth/reset_password/{token} avec un token invalide."""
    invalid_token = "invalidtoken12345"
    new_password = "AnotherPassword789!"

    response = client.post(
        f"/auth/reset_password/{invalid_token}",
        json={"new_password": new_password}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Token invalide ou expiré"}


def test_reset_password_expired_token():
    """Test POST /auth/reset_password/{token} avec un token expiré."""
    user_id, email, old_password = create_temp_user()
    expired_token = uuid.uuid4().hex
    expired_at = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

    # Insérer un token expiré
    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user_id, expired_token, expired_at)
        )
        conn.commit()

    new_password = "ExpiredPassword123!"

    response = client.post(
        f"/auth/reset_password/{expired_token}",
        json={"new_password": new_password}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Token expiré"}

import threading
import pytest
import time
import requests
import uvicorn
from fastapi import FastAPI
import sys
import os
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

FASTAPI_PORT = 8001
BASE_URL = f"http://localhost:{FASTAPI_PORT}"

from app.main import app as fastapi_app


# Fonction utilitaire pour démarrer FastAPI
def start_fastapi():
    # Lancer le serveur Uvicorn avec l'application importée
    uvicorn.run(fastapi_app, host="0.0.0.0", port=FASTAPI_PORT, log_level="info")


# Fixture pour démarrer le serveur FastAPI (au niveau du module)
@pytest.fixture(scope="session", autouse=True)
def fastapi_server_fixture():
    print("\nDémarrage du serveur FastAPI...")
    thread = threading.Thread(target=start_fastapi, daemon=True)
    thread.start()
    time.sleep(1)

    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/docs")
            response.raise_for_status()
            print("Serveur FastAPI démarré et accessible.")
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
            time.sleep(1)
    else:
        pytest.fail("Échec du démarrage du serveur FastAPI après plusieurs tentatives.")
    yield


# La fonction de test d'intégration (au niveau du module)
def test_flask_to_fastapi_register_login_and_dashboard_flow(fastapi_server_fixture):
    # --- Inscription ---
    register_payload = {
        "username": "flask_integration_test",
        "email": "flask@test.com",
        "password": "securePassword123!"
    }

    # Utilisation de 'requests' pour interagir avec le serveur FastAPI démarré
    # Chemin correct: /auth/register
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)

    # 200 pour succès, 400 si email déjà utilisé (selon votre route)
    assert response.status_code in [200, 400], f"Échec de l'inscription : {response.text}"
    # Si l'inscription réussit (status 200), extraire le token
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        assert token, "Token non renvoyé après l'inscription"
    elif response.status_code == 400 and "Email déjà utilisé" in response.text:
        # Si l'email est déjà utilisé, tenter de se connecter pour obtenir un token
        print("Email déjà utilisé, tentative de connexion...")
        login_payload_existing = {
            "email": register_payload["email"],
            "password": register_payload["password"]
        }
        login_response_existing = requests.post(f"{BASE_URL}/auth/login", json=login_payload_existing)
        assert login_response_existing.status_code == 200, f"Échec de la connexion pour utilisateur existant : {login_response_existing.text}"
        token = login_response_existing.json().get("access_token")
        assert token, "Token non renvoyé après la connexion pour utilisateur existant"
    else:
        pytest.fail(f"Échec inattendu lors de l'inscription : {response.status_code} - {response.text}")

    headers = {"Authorization": f"Bearer {token}"}

    # Récupération du dashboard
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    # Le dashboard peut retourner 200 (succès) ou 404 (pas de préférences)
    assert response.status_code in [200, 404], f"Erreur lors de l'accès au dashboard : {response.text}"

    # Obtention des informations utilisateur
    user_info_response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    # La route /users/me retourne l'ID utilisateur si authentifié
    assert user_info_response.status_code == 200, f"Échec de l'obtention des informations utilisateur (/users/me) : {user_info_response.text}"
    user_data = user_info_response.json()

    user_id = user_data.get("user_id")
    assert user_id is not None, "ID utilisateur non trouvé dans la réponse de /users/me"

    # Mise à jour ou création des préférences (route protégée)
    preferences_payload = {
        "source_preferences": ["TechCrunch", "Wired"],
        "video_channel_preferences": ["Two Minute Papers", "Yann LeCun"],
        "keyword_preferences": ["AI", "Machine Learning"]
    }

    # Endpoint POST pour créer/mettre à jour les préférences
    # Chemin correct: /preferences/user-preferences
    response = requests.post(
        f"{BASE_URL}/preferences/user-preferences",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=preferences_payload
    )
    # La route POST /preferences/user-preferences retourne 200 en cas de succès
    assert response.status_code == 200, f"Échec de la mise à jour des préférences : {response.text}"
    assert "message" in response.json()
    assert "Préférences mises à jour avec succès" in response.json()["message"]

    # Récupération du dashboard après mise à jour
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    assert response.status_code == 200, f"Échec de l'accès au dashboard après la mise à jour des préférences : {response.text}"
    data = response.json()

    # Vérifications de la structure et le contenu de la réponse du dashboard
    assert "articles_by_source" in data
    assert isinstance(data["articles_by_source"], list)
    assert "metrics" in data
    assert isinstance(data["metrics"], dict)
    assert "trending_keywords" in data
    assert isinstance(data["trending_keywords"], list)

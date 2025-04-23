import threading
import pytest
import time
import requests
import uvicorn
from fastapi import FastAPI
import sys
import os
from unittest.mock import patch, MagicMock


# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)

FASTAPI_PORT = 8001
BASE_URL = f"http://localhost:{FASTAPI_PORT}"


with patch('mysql.connector.pooling.MySQLConnectionPool'):
    from app.main import app as fastapi_app


# Fonction utilitaire pour démarrer FastAPI
def start_fastapi():
    # Lancer le serveur Uvicorn avec l'application importée
    uvicorn.run(fastapi_app, host="0.0.0.0", port=FASTAPI_PORT, log_level="info")


# Fixture pour démarrer le serveur FastAPI (au niveau du module, sans 'self')
@pytest.fixture(scope="session", autouse=True)
def fastapi_server_fixture():
    print("\nDémarrage du serveur FastAPI...")
    thread = threading.Thread(target=start_fastapi, daemon=True)
    thread.start()
    time.sleep(2)

    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/docs")
            print("Serveur FastAPI démarré.")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        pytest.fail("Échec du démarrage du serveur FastAPI.")

    yield

    print("\nArrêt du serveur FastAPI...")


# La fonction de test d'intégration (au niveau du module, sans 'self')
def test_flask_to_fastapi_register_login_and_dashboard_flow(fastapi_server_fixture):
    # --- Inscription ---
    register_payload = {
        "username": "flask_integration_test",
        "email": "flask@test.com",
        "password": "securePassword123!"
    }

    # Utilisation de 'requests' pour interagir avec le serveur FastAPI démarré
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)

    assert response.status_code in [200, 409], f"Échec de l'inscription : {response.text}"

    # Connexion
    login_payload = {
        "email": register_payload["email"],
        "password": register_payload["password"]
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert response.status_code == 200, f"Échec de la connexion : {response.text}"
    token = response.json().get("access_token")
    assert token, "Token non renvoyé après la connexion"

    headers = {"Authorization": f"Bearer {token}"}

    # Récupération du dashboard
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    assert response.status_code in [200, 404], f"Erreur lors de l'accès au dashboard : {response.text}"

    # Mise à jour ou création des préférences
    user_info_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert user_info_response.status_code == 200, f"Échec de l'obtention des informations utilisateur (/auth/me) : {user_info_response.text}"
    user_id = user_info_response.json().get("user_id")
    assert user_id is not None, "ID utilisateur non trouvé dans la réponse de /auth/me"

    preferences_payload = {
        "source_preferences": ["TechCrunch", "Wired"],
        "video_channel_preferences": ["Two Minute Papers", "Yann LeCun"],
        "keyword_preferences": ["AI", "Machine Learning"]
    }

    # Endpoint PUT pour mettre à jour les préférences
    response = requests.put(
        f"{BASE_URL}/preferences/{user_id}/filters",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=preferences_payload
    )
    assert response.status_code == 200, f"Échec de la mise à jour des préférences : {response.text}"

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

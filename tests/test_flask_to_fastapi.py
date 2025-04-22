import threading
import time
import requests
import uvicorn
from fastapi import FastAPI
from app.main import app as fastapi_app
import pytest

FASTAPI_PORT = 8001
BASE_URL = f"http://localhost:{FASTAPI_PORT}"


# Démarre FastAPI dans un thread à part
def start_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=FASTAPI_PORT, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def fastapi_server():
    thread = threading.Thread(target=start_fastapi, daemon=True)
    thread.start()
    time.sleep(1.5)  # Laisse un peu de temps à FastAPI pour démarrer
    yield
    # Pas besoin d'arrêter explicitement uvicorn en mode test, car daemon


def test_flask_to_fastapi_register_login_and_dashboard_flow(fastapi_server):
    # Inscription
    register_payload = {
        "username": "flask_integration_test",
        "email": "flask@test.com",
        "password": "securePassword123!"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    assert response.status_code in [200, 409], "L'inscription a échoué"

    # Connexion
    login_payload = {
        "username": "flask_integration_test",
        "password": "securePassword123!"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert response.status_code == 200, "La connexion a échoué"
    token = response.json().get("access_token")
    assert token, "Token non renvoyé"

    headers = {"Authorization": f"Bearer {token}"}

    # Récupération du dashboard (sans préférences au départ)
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    assert response.status_code in [200, 404], "Erreur lors de l'accès au dashboard"

    if response.status_code == 404:
        print("Pas de préférences définies — on les met à jour maintenant")

    # Mise à jour des préférences
    user_id = requests.get(f"{BASE_URL}/auth/me", headers=headers).json()["user_id"]
    preferences_payload = {
        "source_preferences": "TechCrunch;Wired",
        "video_channel_preferences": "Two Minute Papers;Yann LeCun",
        "keyword_preferences": "AI;Machine Learning"
    }

    response = requests.put(
        f"{BASE_URL}/preferences/{user_id}/filters",
        headers={"Content-Type": "application/json"},
        json=preferences_payload
    )
    assert response.status_code == 200, "Mise à jour des préférences échouée"

    #  Récupération du dashboard après mise à jour
    response = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    assert response.status_code == 200, "Accès au dashboard après préférences échoué"
    data = response.json()

    assert "articles_by_source" in data
    assert "metrics" in data
    assert "trending_keywords" in data
    assert "trends_chart" in data

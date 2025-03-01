from fastapi import FastAPI, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes import (
    articles_route, videos_route, scientific_articles_route,
    metrics_route, trends_route, auth_route
)
from app.security.password_handler import hash_password, verify_password
from app.security.jwt_handler import jwt_required
import logging

# Initialisation de l'application FastAPI
app = FastAPI()

# Inclusion des routes publiques (non protégées)
app.include_router(auth_route.router, prefix="/auth", tags=["Auth"])

# Inclusion des routes protégées
protected_routes = [
    (articles_route.router, "/articles", "Articles"),
    (videos_route.router, "/videos", "Videos"),
    (scientific_articles_route.router, "/scientific-articles", "Scientific Articles"),
    (metrics_route.router, "/metrics", "Metrics"),
    (trends_route.router, "/trends", "Trends"),
]

for router, prefix, tag in protected_routes:
    app.include_router(router, prefix=prefix, tags=[tag], dependencies=[Depends(jwt_required)])


# Tâche périodique (vérification des alertes)
def check_alerts():
    """Vérifie les alertes pour les utilisateurs (remplacer par ta logique)."""
    logging.info("Vérification des alertes en cours...")


# Configuration du scheduler pour exécuter la tâche toutes les 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(check_alerts, 'interval', minutes=10)
scheduler.start()


# Gestion propre de l'arrêt du scheduler
@app.on_event("shutdown")
def shutdown_scheduler():
    logging.info("Arrêt du scheduler...")
    scheduler.shutdown()


# Route principale
@app.get("/")
async def root():
    """Point d'entrée de l'API."""
    return {"message": "Bienvenue sur l'API Veille IA !"}

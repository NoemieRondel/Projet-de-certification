from fastapi import FastAPI, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes import (
    articles_route, videos_route, scientific_articles_route,
    metrics_route, trends_route, auth_route, user_preferences_route,
    dashboard_route, user_delete_route, forgot_password_route, reset_password_route
)
from app.security.jwt_handler import jwt_required
import logging

# Initialisation de FastAPI
app = FastAPI()

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inclusion des routes publiques
app.include_router(auth_route.router, prefix="/auth", tags=["Auth"])

# Inclusion des routes protégées
protected_routes = [
    (articles_route.router, "/articles", "Articles"),
    (videos_route.router, "/videos", "Videos"),
    (scientific_articles_route.router, "/scientific-articles", "Scientific Articles"),
    (metrics_route.router, "/metrics", "Metrics"),
    (trends_route.router, "/trends", "Trends"),
    (user_preferences_route.router, "/preferences", "User Preferences"),
    (dashboard_route.router, "/dashboard", "Dashboard")
]

# Routes protégées pour la suppression de l'utilisateur ou le reset de mot de passe
app.include_router(user_delete_route.router, prefix="/users", tags=["User"], dependencies=[Depends(jwt_required)])
app.include_router(forgot_password_route.router, prefix="/auth", tags=["Auth"])
app.include_router(reset_password_route.router, prefix="/auth", tags=["Auth"])

for router, prefix, tag in protected_routes:
    app.include_router(router, prefix=prefix, tags=[tag], dependencies=[Depends(jwt_required)])


# Fonction pour vérifier les alertes
def check_alerts():
    """Vérifie les alertes pour les utilisateurs (remplacer par ta logique)."""
    logger.info("Vérification des alertes en cours...")


# Démarrage du scheduler de manière sécurisée
try:
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_alerts, 'interval', minutes=10)
    scheduler.start()
    logger.info("Scheduler démarré avec succès.")
except Exception as e:
    logger.error(f"Erreur lors du démarrage du scheduler : {e}")


# Gestion propre de l'arrêt du scheduler
@app.on_event("shutdown")
def shutdown_scheduler():
    logger.info("Arrêt du scheduler...")
    scheduler.shutdown()


# Route principale
@app.get("/")
async def root():
    """Point d'entrée de l'API."""
    return {"message": "Bienvenue sur l'API Veille IA !"}

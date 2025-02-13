from fastapi import FastAPI, Depends
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes import articles_route, videos_route, scientific_articles_route, metrics_route, trends_route
from app.security.jwt_handler import jwt_required
import logging

# Initialisation de l'application FastAPI
app = FastAPI()

# Inclusion des routes avec protection JWT pour toutes les routes
app.include_router(articles_route.router, prefix="/articles", tags=["Articles"], dependencies=[Depends(jwt_required)])
app.include_router(videos_route.router, prefix="/videos", tags=["Videos"], dependencies=[Depends(jwt_required)])
app.include_router(scientific_articles_route.router, prefix="/scientific-articles", tags=["Scientific Articles"], dependencies=[Depends(jwt_required)])
app.include_router(metrics_route.router, prefix="/metrics", tags=["Metrics"], dependencies=[Depends(jwt_required)])
app.include_router(trends_route.router, prefix="/trends", tags=["Trends"], dependencies=[Depends(jwt_required)])


# Fonction de tâche périodique pour vérifier les alertes
def check_alerts():
    """Vérifie les alertes pour les utilisateurs (remplacer par ta logique)."""
    logging.info("Vérification des alertes en cours...")  # Utilisation du logging pour un suivi


# Configuration du scheduler pour exécuter la tâche toutes les 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(check_alerts, 'interval', minutes=10)  # Toutes les 10 min
scheduler.start()


@app.get("/")
async def root():
    """Point d'entrée de l'API."""
    return {"message": "Bienvenue sur l'API Veille IA !"}

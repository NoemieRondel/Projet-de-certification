from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter()

# Initialisation du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Modèle de réponse pour les vidéos
class VideoResponse(BaseModel):
    id: int
    title: str
    video_url: str
    channel_name: str
    publication_date: str  # Format YYYY-MM-DD
    description: Optional[str]


# Fonction de validation de date
def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format de date invalide : {date_str}. Utilisez YYYY-MM-DD.")


# Route pour récupérer toutes les vidéos avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère toutes les vidéos avec filtres dynamiques",
    response_model=List[VideoResponse],
    responses={
        200: {"description": "Liste des vidéos récupérées."},
        404: {"description": "Aucune vidéo trouvée."},
        500: {"description": "Erreur interne."}
    }
)
async def get_all_videos(
    start_date: Optional[str] = Query(None, description="Filtrer les vidéos à partir de cette date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filtrer les vidéos jusqu'à cette date (YYYY-MM-DD)"),
    channel_name: Optional[str] = Query(None, description="Filtrer par chaîne (channel_name)"),
    user=Depends(jwt_required)
):
    """Récupère les vidéos avec filtres dynamiques."""

    query = """
        SELECT id, title, video_url, channel_name, publication_date, description
        FROM videos
        WHERE 1=1
    """
    params = []

    if start_date:
        start_date = validate_date(start_date)
        query += " AND publication_date >= %s"
        params.append(start_date)

    if end_date:
        end_date = validate_date(end_date)
        query += " AND publication_date <= %s"
        params.append(end_date)

    if channel_name:
        query += " AND channel_name = %s"
        params.append(channel_name)

    logger.info(f"Requête SQL : {query}")
    logger.info(f"Paramètres : {params}")

    # Connexion à la base de données
    try:
        connection = get_connection()
        if not connection:
            raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            videos = cursor.fetchall()

            if not videos:
                raise HTTPException(status_code=404, detail="Aucune vidéo trouvée.")

            # Conversion de publication_date en string avant la réponse
            for video in videos:
                video['publication_date'] = video['publication_date'].strftime('%Y-%m-%d')

            return videos

    except Exception as e:
        logger.error(f"Erreur SQL : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")

    finally:
        connection.close()

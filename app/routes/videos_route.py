from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# Modèle de réponse pour les vidéos
class VideoResponse(BaseModel):
    id: int
    title: str
    url: str
    channel_name: str
    publication_date: str
    keywords: Optional[str]


# Route pour récupérer toutes les vidéos avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère toutes les vidéos avec filtres dynamiques",
    response_model=List[VideoResponse],  # 🔥 Structure propre de la sortie
    responses={
        200: {"description": "Liste des vidéos récupérées."},
        404: {"description": "Aucune vidéo trouvée."},
        500: {"description": "Erreur interne."}
    }
)
async def get_all_videos(
    start_date: str = Query(None, description="Filtrer les vidéos à partir de cette date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Filtrer les vidéos jusqu'à cette date (YYYY-MM-DD)"),
    channel_name: str = Query(None, description="Filtrer par chaîne (channel_name)"),
    user=Depends(jwt_required)  # 🔒 Protection avec JWT
):
    """Récupère les vidéos avec filtres dynamiques."""
    query = """
        SELECT id, title, url, channel_name, publication_date, keywords
        FROM videos
        WHERE 1=1
    """
    params = []

    # Ajout des filtres dynamiquement
    if start_date:
        query += " AND publication_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND publication_date <= %s"
        params.append(end_date)

    if channel_name:
        query += " AND channel_name = %s"
        params.append(channel_name)

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            videos = cursor.fetchall()

            if not videos:
                raise HTTPException(status_code=404, detail="Aucune vidéo trouvée.")

            return videos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


# Route pour récupérer les 10 dernières vidéos publiées
@router.get(
    "/latest",
    summary="Dernières vidéos publiées",
    response_model=List[VideoResponse],  # 🔥 Structure propre de la sortie
    responses={
        200: {"description": "Liste des 10 dernières vidéos."},
        500: {"description": "Erreur interne."}
    }
)
async def get_latest_videos(user=Depends(jwt_required)):  
    """Retourne les 10 dernières vidéos publiées."""
    query = """
        SELECT id, title, url, channel_name, publication_date, keywords
        FROM videos
        ORDER BY publication_date DESC
        LIMIT 10
    """

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query)
            latest_videos = cursor.fetchall()

            if not latest_videos:
                raise HTTPException(status_code=404, detail="Aucune vidéo trouvée.")

            return latest_videos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


# Route pour récupérer les suggestions de chaînes (channel_name)
@router.get(
    "/suggestions",
    summary="Suggestions de chaînes pour filtrer les vidéos",
    responses={
        200: {"description": "Suggestions récupérées."},
        500: {"description": "Erreur interne."}
    }
)
async def get_suggestions_videos(user=Depends(jwt_required)):  
    """Retourne les suggestions de chaînes (channel_name)."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute("SELECT DISTINCT channel_name FROM videos WHERE channel_name IS NOT NULL")
            channels = [row["channel_name"] for row in cursor.fetchall()]

            return {"channel_names": channels}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()

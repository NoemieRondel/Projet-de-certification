from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required

router = APIRouter()


# Route existante pour récupérer toutes les vidéos avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère toutes les vidéos avec filtres dynamiques",
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
    user=Depends(jwt_required)  # Protection avec JWT
):
    """Récupère les vidéos avec filtres dynamiques."""
    query = "SELECT * FROM videos WHERE 1=1"
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
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query, params)
                videos = cursor.fetchall()

                if not videos:
                    raise HTTPException(status_code=404, detail="Aucune vidéo trouvée.")

                return {"data": videos}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")


# Nouvelle route pour récupérer les 10 dernières vidéos publiées
@router.get(
    "/latest",
    summary="Dernières vidéos",
    description="Retourne les 10 dernières vidéos publiées.",
    responses={
        200: {"description": "Liste des 10 dernières vidéos."},
        500: {"description": "Erreur interne."}
    }
)
async def get_latest_videos(user=Depends(jwt_required)):  
    """Retourne les 10 dernières vidéos publiées."""
    query = """
        SELECT title, url, published_at
        FROM videos
        ORDER BY published_at DESC
        LIMIT 10
    """

    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                latest_videos = cursor.fetchall()

                if not latest_videos:
                    raise HTTPException(status_code=404, detail="Aucune vidéo trouvée.")

                return {"data": latest_videos}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")


# Route existante pour les suggestions de chaînes (channel_name)
@router.get(
    "/suggestions",
    summary="Suggestions pour les filtres channel_name",
    responses={
        200: {"description": "Suggestions récupérées."},
        500: {"description": "Erreur interne."}
    }
)
async def get_suggestions_videos(user=Depends(jwt_required)):
    """Retourne les suggestions pour les chaînes (channel_name)."""
    suggestions = {
        "channel_names": []
    }

    query_channel_names = "SELECT DISTINCT channel_name FROM videos"

    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                # Récupérer les suggestions de channel_name
                cursor.execute(query_channel_names)
                channel_name_results = cursor.fetchall()
                suggestions["channel_names"] = [entry["channel_name"] for entry in channel_name_results if entry["channel_name"]]

            return {"data": suggestions}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

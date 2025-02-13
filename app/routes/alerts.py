from fastapi import APIRouter, HTTPException, Body
from app.database import get_connection
from contextlib import closing

router = APIRouter()

@router.put("/preferences/{user_id}/filters", summary="Mise à jour des préférences de filtrage")
async def update_user_preferences(
    user_id: int,
    source_preferences: str = Body(..., description="Préférences des sources d'information"),
    video_channel_preferences: str = Body(..., description="Préférences des chaînes vidéo"),
    keyword_preferences: str = Body(..., description="Préférences des mots-clés")
):
    """Met à jour les préférences de filtrage pour un utilisateur."""
    query = """
        UPDATE user_preferences
        SET source_preferences = %s, video_channel_preferences = %s, keyword_preferences = %s
        WHERE user_id = %s
    """
    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, (source_preferences, video_channel_preferences, keyword_preferences, user_id))
                connection.commit()
                return {"message": "Préférences de filtrage mises à jour avec succès."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

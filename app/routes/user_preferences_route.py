from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing
from typing import List, Optional

router = APIRouter()


class UserPreferencesUpdate(BaseModel):
    source_preferences: Optional[List[str]] = None
    video_channel_preferences: Optional[List[str]] = None
    keyword_preferences: Optional[List[str]] = None


def get_available_filters():
    """Récupère les valeurs autorisées pour les sources, chaînes vidéo et mots-clés."""
    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT DISTINCT source FROM articles")
        sources = [row["source"] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT channel_name FROM videos")
        channels = [row["channel_name"] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT keywords FROM articles WHERE keywords IS NOT NULL")
        article_keywords = [keyword for row in cursor.fetchall() for keyword in row["keywords"].split(';')]

        cursor.execute("SELECT DISTINCT keywords FROM scientific_articles WHERE keywords IS NOT NULL")
        scientific_article_keywords = [keyword for row in cursor.fetchall() for keyword in row["keywords"].split(';')]

        keywords = list(set(article_keywords + scientific_article_keywords))

    return {"articles": sources, "videos": channels, "keywords": keywords}


@router.get("/user-preferences")
def get_user_preferences(user=Depends(jwt_required)):
    """Récupère les préférences de l'utilisateur + les options disponibles."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    available_filters = get_available_filters()

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT source_preferences, video_channel_preferences, keyword_preferences "
            "FROM user_preferences WHERE user_id = %s", (user_id,)
        )
        result = cursor.fetchone()

    user_prefs = {
        "source_preferences": result["source_preferences"].split(";") if result and result["source_preferences"] else [],
        "video_channel_preferences": result["video_channel_preferences"].split(";") if result and result["video_channel_preferences"] else [],
        "keyword_preferences": result["keyword_preferences"].split(";") if result and result["keyword_preferences"] else [],
    }

    return {
        "user_preferences": user_prefs,
        "available_filters": available_filters
    }


@router.post("/user-preferences")
def update_user_preferences(user=Depends(jwt_required), preferences: UserPreferencesUpdate = Depends()):
    """Met à jour les préférences utilisateur après validation stricte."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    valid_filters = get_available_filters()

    def validate_choices(choices, valid_list, category):
        if choices:
            invalid = [choice for choice in choices if choice not in valid_list]
            if invalid:
                raise HTTPException(status_code=400, detail=f"Valeurs non valides pour {category}: {invalid}")

    validate_choices(preferences.source_preferences, valid_filters["articles"], "source_preferences")
    validate_choices(preferences.video_channel_preferences, valid_filters["videos"], "video_channel_preferences")
    validate_choices(preferences.keyword_preferences, valid_filters["keywords"], "keyword_preferences")

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT source_preferences, video_channel_preferences, keyword_preferences FROM user_preferences WHERE user_id = %s",
            (user_id,)
        )
        existing_prefs = cursor.fetchone()

        existing_sources = existing_prefs["source_preferences"].split(";") if existing_prefs and existing_prefs["source_preferences"] else []
        existing_videos = existing_prefs["video_channel_preferences"].split(";") if existing_prefs and existing_prefs["video_channel_preferences"] else []
        existing_keywords = existing_prefs["keyword_preferences"].split(";") if existing_prefs and existing_prefs["keyword_preferences"] else []

        updated_sources = list(set(existing_sources + (preferences.source_preferences or [])))
        updated_videos = list(set(existing_videos + (preferences.video_channel_preferences or [])))
        updated_keywords = list(set(existing_keywords + (preferences.keyword_preferences or [])))

        source_prefs = ";".join(updated_sources) if updated_sources else None
        video_prefs = ";".join(updated_videos) if updated_videos else None
        keyword_prefs = ";".join(updated_keywords) if updated_keywords else None

        if existing_prefs:
            cursor.execute(
                "UPDATE user_preferences SET source_preferences = %s, video_channel_preferences = %s, keyword_preferences = %s "
                "WHERE user_id = %s",
                (source_prefs, video_prefs, keyword_prefs, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO user_preferences (user_id, source_preferences, video_channel_preferences, keyword_preferences) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, source_prefs, video_prefs, keyword_prefs)
            )

        conn.commit()

    return {"message": "Préférences mises à jour avec succès"}


@router.delete("/user-preferences")
def delete_user_preferences(user=Depends(jwt_required), preferences: UserPreferencesUpdate = Depends()):
    """Supprime certaines préférences utilisateur ou toutes si aucun filtre n'est fourni."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT source_preferences, video_channel_preferences, keyword_preferences FROM user_preferences WHERE user_id = %s",
            (user_id,)
        )
        existing_prefs = cursor.fetchone()

        if not existing_prefs:
            raise HTTPException(status_code=404, detail="Aucune préférence trouvée pour cet utilisateur.")

        existing_sources = existing_prefs["source_preferences"].split(";") if existing_prefs["source_preferences"] else []
        existing_videos = existing_prefs["video_channel_preferences"].split(";") if existing_prefs["video_channel_preferences"] else []
        existing_keywords = existing_prefs["keyword_preferences"].split(";") if existing_prefs["keyword_preferences"] else []

        if preferences.source_preferences:
            existing_sources = [s for s in existing_sources if s not in preferences.source_preferences]
        if preferences.video_channel_preferences:
            existing_videos = [v for v in existing_videos if v not in preferences.video_channel_preferences]
        if preferences.keyword_preferences:
            existing_keywords = [k for k in existing_keywords if k not in preferences.keyword_preferences]

        if not preferences.source_preferences and not preferences.video_channel_preferences and not preferences.keyword_preferences:
            cursor.execute(
                "DELETE FROM user_preferences WHERE user_id = %s",
                (user_id,)
            )
        else:
            cursor.execute(
                "UPDATE user_preferences SET source_preferences = %s, video_channel_preferences = %s, keyword_preferences = %s WHERE user_id = %s",
                (
                    ";".join(existing_sources) if existing_sources else None,
                    ";".join(existing_videos) if existing_videos else None,
                    ";".join(existing_keywords) if existing_keywords else None,
                    user_id
                )
            )

        conn.commit()

    return {"message": "Préférences mises à jour après suppression"}

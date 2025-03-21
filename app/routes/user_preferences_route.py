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
        # Récupérer les sources de la table articles
        cursor.execute("SELECT DISTINCT source FROM articles")
        sources = [row["source"] for row in cursor.fetchall()]

        # Récupérer les noms de chaînes de la table videos
        cursor.execute("SELECT DISTINCT channel_name FROM videos")
        channels = [row["channel_name"] for row in cursor.fetchall()]

        # Récupérer les mots-clés de la table articles
        cursor.execute("SELECT DISTINCT keywords FROM articles WHERE keywords IS NOT NULL")
        article_keywords = [keyword for row in cursor.fetchall() for keyword in row["keywords"].split(';')]

        # Récupérer les mots-clés de la table scientific_articles
        cursor.execute("SELECT DISTINCT keywords FROM scientific_articles WHERE keywords IS NOT NULL")
        scientific_article_keywords = [keyword for row in cursor.fetchall() for keyword in row["keywords"].split(';')]

        # Fusionner et nettoyer les doublons
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
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")  # Récupération de l'ID utilisateur depuis le JWT
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
        # Récupérer les préférences existantes
        cursor.execute(
            "SELECT source_preferences, video_channel_preferences, keyword_preferences FROM user_preferences WHERE user_id = %s",
            (user_id,)
        )
        existing_prefs = cursor.fetchone()

        # Convertir les valeurs en listes (si elles existent)
        existing_sources = existing_prefs["source_preferences"].split(";") if existing_prefs and existing_prefs["source_preferences"] else []
        existing_videos = existing_prefs["video_channel_preferences"].split(";") if existing_prefs and existing_prefs["video_channel_preferences"] else []
        existing_keywords = existing_prefs["keyword_preferences"].split(";") if existing_prefs and existing_prefs["keyword_preferences"] else []

        # Fusionner les préférences existantes avec les nouvelles (en évitant les doublons)
        updated_sources = list(set(existing_sources + (preferences.source_preferences or [])))
        updated_videos = list(set(existing_videos + (preferences.video_channel_preferences or [])))
        updated_keywords = list(set(existing_keywords + (preferences.keyword_preferences or [])))

        # Convertir en format pour la base de données (chaîne séparée par des ";")
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

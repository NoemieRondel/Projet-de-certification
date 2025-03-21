from fastapi import APIRouter, Depends, HTTPException
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(user=Depends(jwt_required)):
    """Récupère les derniers articles, vidéos et statistiques de tendances pour l'utilisateur."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        # Récupérer les préférences de l'utilisateur
        cursor.execute(
            "SELECT source_preferences, video_channel_preferences, keyword_preferences "
            "FROM user_preferences WHERE user_id = %s", (user_id,)
        )
        user_prefs = cursor.fetchone()

        if not user_prefs:
            raise HTTPException(status_code=404, detail="No preferences found for user")

        sources = user_prefs["source_preferences"].split(";") if user_prefs["source_preferences"] else []
        channels = user_prefs["video_channel_preferences"].split(";") if user_prefs["video_channel_preferences"] else []
        keywords = user_prefs["keyword_preferences"].split(";") if user_prefs["keyword_preferences"] else []

        # Récupérer les derniers articles en fonction des sources préférées
        latest_articles_by_source = []
        if sources:
            query = "SELECT id, title, source, url, published_at FROM articles WHERE source IN ({}) ORDER BY published_at DESC LIMIT 10".format(
                ",".join(["%s"] * len(sources))
            )
            cursor.execute(query, sources)
            latest_articles_by_source = cursor.fetchall()

        # Récupérer les derniers articles en fonction des mots-clés préférés
        latest_articles_by_keywords = []
        latest_scientific_articles_by_keywords = []
        if keywords:
            keyword_filters = " OR ".join(["keywords LIKE %s"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]

            # Articles généraux avec les mots-clés
            query = f"SELECT id, title, source, url, published_at FROM articles WHERE {keyword_filters} ORDER BY published_at DESC LIMIT 10"
            cursor.execute(query, params)
            latest_articles_by_keywords = cursor.fetchall()

            # Articles scientifiques avec les mots-clés
            query = f"SELECT id, title, journal, url, published_at FROM scientific_articles WHERE {keyword_filters} ORDER BY published_at DESC LIMIT 10"
            cursor.execute(query, params)
            latest_scientific_articles_by_keywords = cursor.fetchall()

        # Récupérer les dernières vidéos des chaînes préférées
        latest_videos = []
        if channels:
            query = "SELECT id, title, channel_name, url, published_at FROM videos WHERE channel_name IN ({}) ORDER BY published_at DESC LIMIT 10".format(
                ",".join(["%s"] * len(channels))
            )
            cursor.execute(query, channels)
            latest_videos = cursor.fetchall()

        # Statistiques des tendances des mots-clés sur les 30 derniers jours
        date_threshold = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT IFNULL(keywords, '') AS keywords FROM articles WHERE published_at >= %s",
            (date_threshold,)
        )
        all_keywords = [
            kw for row in cursor.fetchall() if row["keywords"]
            for kw in row["keywords"].split(";")
        ]
        trending_keywords = Counter(all_keywords).most_common(10)  # Top 10

        # Filtrer uniquement les tendances des mots-clés préférés
        if keywords:
            trending_keywords = [(kw, count) for kw, count in trending_keywords if kw in keywords]

    return {
        "articles_by_source": latest_articles_by_source,
        "articles_by_keywords": latest_articles_by_keywords,
        "scientific_articles_by_keywords": latest_scientific_articles_by_keywords,
        "latest_videos": latest_videos,
        "trending_keywords": [{"keyword": kw, "count": count} for kw, count in trending_keywords],
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter()


@router.get("/")
def get_dashboard(
    user=Depends(jwt_required),
    limit: int = Query(10, ge=1, le=50, description="Nombre d'éléments à récupérer (1-50)")
):
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
        articles_count = 0
        if sources:
            query = f"""
                SELECT id, title, source, link, publication_date, keywords
                FROM articles 
                WHERE source IN ({",".join(["%s"] * len(sources))}) 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, sources + [limit])
            latest_articles_by_source = cursor.fetchall()

            # Comptage des articles par source
            query = f"SELECT COUNT(*) AS count FROM articles WHERE source IN ({','.join(['%s'] * len(sources))})"
            cursor.execute(query, sources)
            articles_count = cursor.fetchone()["count"]

        # Récupérer les derniers articles en fonction des mots-clés préférés
        latest_articles_by_keywords = []
        latest_scientific_articles_by_keywords = []
        scientific_articles_count = 0
        if keywords:
            keyword_filters = " OR ".join(["keywords LIKE %s"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]

            # Articles généraux avec les mots-clés
            query = f"""
                SELECT id, title, source, link, publication_date, keywords 
                FROM articles 
                WHERE {keyword_filters} 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, params + [limit])
            latest_articles_by_keywords = cursor.fetchall()

            # Comptage des articles avec mots-clés
            query = f"SELECT COUNT(*) AS count FROM articles WHERE {keyword_filters}"
            cursor.execute(query, params)
            articles_count += cursor.fetchone()["count"]

            # Articles scientifiques avec les mots-clés
            query = f"""
                SELECT id, title, abstract, article_url, publication_date, keywords, authors
                FROM scientific_articles 
                WHERE {keyword_filters} 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, params + [limit])
            latest_scientific_articles_by_keywords = cursor.fetchall()

            # Comptage des articles scientifiques
            query = f"SELECT COUNT(*) AS count FROM scientific_articles WHERE {keyword_filters}"
            cursor.execute(query, params)
            scientific_articles_count = cursor.fetchone()["count"]

        # Récupérer les dernières vidéos des chaînes préférées
        latest_videos = []
        videos_count = 0
        if channels:
            query = f"""
                SELECT id, title, source, video_url, publication_date
                FROM videos 
                WHERE channel_name IN ({",".join(["%s"] * len(channels))}) 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, channels + [limit])
            latest_videos = cursor.fetchall()

            # Comptage des vidéos par chaîne
            query = f"SELECT COUNT(*) AS count FROM videos WHERE source IN ({','.join(['%s'] * len(channels))})"
            cursor.execute(query, channels)
            videos_count = cursor.fetchone()["count"]

        # Statistiques des tendances des mots-clés sur les 30 derniers jours
        date_threshold = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT IFNULL(keywords, '') AS keywords FROM articles WHERE publication_date >= %s",
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
        "metrics": {
            "articles_count": articles_count,
            "videos_count": videos_count,
            "scientific_articles_count": scientific_articles_count,
        }
    }

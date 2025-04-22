from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing

router = APIRouter()


@router.get("/")
def get_dashboard(
    user=Depends(jwt_required),
    limit: int = Query(10, ge=1, le=50, description="Nombre d'éléments à récupérer (1-50)"),
    days_range: int = Query(90, ge=30, le=365, description="Plage de jours à analyser (30-365)")
):
    """Récupère les articles, vidéos et tendances des mots-clés pour un utilisateur."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        #  Récupérer les préférences de l'utilisateur
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

        #  Récupérer les derniers articles en fonction des sources
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

            query = f"SELECT COUNT(*) AS count FROM articles WHERE source IN ({','.join(['%s'] * len(sources))})"
            cursor.execute(query, sources)
            articles_count = cursor.fetchone()["count"]

        #  Récupérer les articles liés aux mots-clés préférés
        latest_articles_by_keywords = []
        latest_scientific_articles_by_keywords = []
        scientific_articles_count = 0
        if keywords:
            keyword_filters = " OR ".join(["keywords LIKE %s"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]

            query = f"""
                SELECT id, title, source, link, publication_date, keywords 
                FROM articles 
                WHERE {keyword_filters} 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, params + [limit])
            latest_articles_by_keywords = cursor.fetchall()

            query = f"SELECT COUNT(*) AS count FROM articles WHERE {keyword_filters}"
            cursor.execute(query, params)
            articles_count += cursor.fetchone()["count"]

            query = f"""
                SELECT id, title, abstract, article_url, publication_date, keywords, authors
                FROM scientific_articles 
                WHERE {keyword_filters} 
                ORDER BY publication_date DESC 
                LIMIT %s
            """
            cursor.execute(query, params + [limit])
            latest_scientific_articles_by_keywords = cursor.fetchall()

            query = f"SELECT COUNT(*) AS count FROM scientific_articles WHERE {keyword_filters}"
            cursor.execute(query, params)
            scientific_articles_count = cursor.fetchone()["count"]

        #  Récupérer les dernières vidéos des chaînes préférées
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

            query = f"SELECT COUNT(*) AS count FROM videos WHERE source IN ({','.join(['%s'] * len(channels))})"
            cursor.execute(query, channels)
            videos_count = cursor.fetchone()["count"]

        #  Calcul des tendances des mots-clés sur une plage dynamique
        date_threshold = (datetime.now() - timedelta(days=days_range)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT IFNULL(keywords, '') AS keywords, publication_date "
            "FROM articles WHERE publication_date >= %s",
            (date_threshold,)
        )

        keyword_by_date = defaultdict(lambda: defaultdict(int))

        for row in cursor.fetchall():
            keywords_list = row["keywords"].split(";") if row["keywords"] else []

            publication_date = row["publication_date"]
            if isinstance(publication_date, datetime):
                date = publication_date.date()
            elif isinstance(publication_date, str):
                try:
                    date = datetime.strptime(publication_date, "%Y-%m-%d").date()
                except ValueError:
                    continue
            else:
                continue

            for keyword in keywords_list:
                keyword_by_date[date][keyword] += 1

        trending_keywords_by_date = []
        keyword_evolution = defaultdict(list)
        all_dates = sorted(keyword_by_date.keys())

        for date in all_dates:
            sorted_keywords = sorted(keyword_by_date[date].items(), key=lambda x: x[1], reverse=True)
            trending_keywords_by_date.append({
                "date": date.strftime("%Y-%m-%d"),
                "keywords": [{"keyword": kw, "count": count} for kw, count in sorted_keywords]
            })

            for keyword in keywords:
                keyword_evolution[keyword].append(keyword_by_date[date].get(keyword, 0))

        trends_chart = {
            "dates": [date.strftime("%Y-%m-%d") for date in all_dates],
            "keyword_trends": [{"keyword": kw, "counts": keyword_evolution[kw]} for kw in keywords]
        }

    return {
        "articles_by_source": latest_articles_by_source,
        "articles_by_keywords": latest_articles_by_keywords,
        "scientific_articles_by_keywords": latest_scientific_articles_by_keywords,
        "latest_videos": latest_videos,
        "trending_keywords": trending_keywords_by_date,
        "metrics": {
            "articles_count": articles_count,
            "videos_count": videos_count,
            "scientific_articles_count": scientific_articles_count,
        },
        "trends_chart": trends_chart
    }

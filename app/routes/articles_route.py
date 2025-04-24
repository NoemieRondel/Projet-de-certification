from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter()


# Modèle de réponse optimisé
class ArticleResponse(BaseModel):
    id: int
    title: str
    source: str
    publication_date: str   # Publication date as string
    keywords: Optional[str]
    summary: Optional[str]
    link: str


# Fonction de validation de date
def validate_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format de date invalide : {date_str}. Utilisez YYYY-MM-DD.")


# Route pour récupérer tous les articles avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère tous les articles",
    response_model=List[ArticleResponse],
    responses={
        200: {"description": "Liste des articles récupérés."},
        404: {"description": "Aucun article trouvé."},
        500: {"description": "Erreur interne."}
    }
)
async def get_all_articles(
    start_date: str = Query(None, description="Filtrer les articles à partir de cette date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Filtrer les articles jusqu'à cette date (YYYY-MM-DD)"),
    source: str = Query(None, description="Filtrer par source"),
    keywords: str = Query(None, description="Filtrer par mots-clés (séparés par des virgules)"),
    user=Depends(jwt_required)
):
    """Récupère les articles avec filtres dynamiques."""

    # Initialisation de la requête de base
    query = """
        SELECT id, title, source, publication_date, keywords, summary, link
        FROM articles WHERE 1=1
    """
    params = []

    # Appliquer les filtres si présents
    if start_date:
        query += " AND publication_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND publication_date <= %s"
        params.append(end_date)

    if source:
        query += " AND source = %s"
        params.append(source)

    if keywords:
        keyword_list = [f"%{kw.strip()}%" for kw in keywords.split(',')]
        query += " AND (" + " OR ".join(["keywords LIKE %s"] * len(keyword_list)) + ")"
        params.extend(keyword_list)

    # Ajout du tri par date (du plus récent au plus ancien)
    query += " ORDER BY publication_date DESC"

    # Connexion à la base de données
    connection = get_connection()
    if not connection:
        logging.error("Impossible de se connecter à la base de données.")
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            logging.info(f"Exécution de la requête : {query} avec les paramètres : {params}")
            cursor.execute(query, params)
            articles = cursor.fetchall()

            if not articles:
                logging.warning("Aucun article trouvé.")
                raise HTTPException(status_code=404, detail="Aucun article trouvé.")

            # Conversion de publication_date en string avant la réponse
            for article in articles:
                article['publication_date'] = article['publication_date'].strftime('%Y-%m-%d')

            return articles

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


# Route pour récupérer les derniers articles par source
@router.get(
    "/latest",
    summary="Récupère le(s) dernier(s) article(s) par source",
    response_model=List[ArticleResponse],
    responses={
        200: {"description": "Liste des derniers articles par source."},
        404: {"description": "Aucun article trouvé."},
        500: {"description": "Erreur interne."}
    }
)
async def get_latest_articles(user=Depends(jwt_required)):
    """Récupère le(s) dernier(s) article(s) pour chaque source."""

    # Requête pour obtenir le dernier article par source
    query = """
        WITH ranked_articles AS (
            SELECT
                id, title, source, publication_date, keywords, summary, link,
                RANK() OVER (PARTITION BY source ORDER BY publication_date DESC) AS rank
            FROM articles
        )
        SELECT id, title, source, publication_date, keywords, summary, link
        FROM ranked_articles
        WHERE rank = 1
        ORDER BY publication_date DESC;
    """

    connection = get_connection()
    if not connection:
        logging.error("Impossible de se connecter à la base de données.")
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            logging.info(f"Exécution de la requête pour les derniers articles : {query}")
            cursor.execute(query)
            articles = cursor.fetchall()

            if not articles:
                logging.warning("Aucun article trouvé.")
                raise HTTPException(status_code=404, detail="Aucun article trouvé.")

            # Conversion de publication_date en string avant la réponse
            for article in articles:
                article['publication_date'] = article['publication_date'].strftime('%Y-%m-%d')

            return articles

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()

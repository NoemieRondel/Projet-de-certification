from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()


# Modèles de réponse
class ArticleSourceMetrics(BaseModel):
    source: str
    count: int


class KeywordFrequencyMetrics(BaseModel):
    keywords: str
    count: int


class PublicationsByPeriodMetrics(BaseModel):
    date: str
    count: int


# Nombre d'articles par source
@router.get(
    "/articles-by-source",
    summary="Nombre d'articles par source",
    response_model=List[ArticleSourceMetrics],
    responses={
        200: {"description": "Nombre d'articles par source récupéré avec succès."},
        500: {"description": "Erreur interne."}
    }
)
async def get_articles_by_source(user=Depends(jwt_required)):
    """Retourne le nombre d'articles pour chaque source."""
    query = """
        SELECT source, COUNT(*) as count
        FROM articles
        GROUP BY source
    """
    return await execute_query(query)


# Fréquence des mots-clés
@router.get(
    "/keyword-frequency",
    summary="Fréquence des mots-clés",
    response_model=List[KeywordFrequencyMetrics],
    responses={
        200: {"description": "Fréquence des mots-clés récupérée avec succès."},
        500: {"description": "Erreur interne."}
    }
)
async def get_keyword_frequency(user=Depends(jwt_required)):
    """Retourne la fréquence d'apparition des mots-clés dans les articles."""
    query = """
        SELECT keywords, COUNT(*) as count
        FROM articles
        GROUP BY keywords
    """
    return await execute_query(query)


# Distribution des publications par période
@router.get(
    "/publications-by-period",
    summary="Distribution des publications par période",
    response_model=List[PublicationsByPeriodMetrics],
    responses={
        200: {"description": "Distribution des publications récupérée avec succès."},
        500: {"description": "Erreur interne."}
    }
)
async def get_publications_by_period(user=Depends(jwt_required)):
    """Retourne la distribution des publications par période."""
    query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM articles
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """
    return await execute_query(query)


# Fonction générique pour exécuter les requêtes
async def execute_query(query: str) -> List[Dict]:
    """Exécute une requête SQL et retourne le résultat sous forme de liste de dictionnaires."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()

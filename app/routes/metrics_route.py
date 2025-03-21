from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Dict, Any
from pydantic import BaseModel

router = APIRouter()


# Modèles de réponse

class SourceMetrics(BaseModel):
    source: str
    count: int


class KeywordFrequencyMetrics(BaseModel):
    keyword: str
    count: int


class PublicationsByPeriodMetrics(BaseModel):
    publication_date: str
    count: int


class TopKeywordsBySourceMetrics(BaseModel):
    source: str
    keyword: str
    count: int


# Exemple de route pour les publications par période
@router.get("/publications-by-period", response_model=List[PublicationsByPeriodMetrics])
async def get_publications_by_period(user=Depends(jwt_required)):
    query = """
        SELECT publication_date, COUNT(*) as count
        FROM articles
        GROUP BY publication_date
        ORDER BY publication_date
    """
    return await execute_query(query)


# Nombre d'articles par source
@router.get("/articles-by-source", response_model=List[SourceMetrics])
async def get_articles_by_source(user=Depends(jwt_required)):
    query = """
        SELECT source, COUNT(*) as count
        FROM articles
        GROUP BY source
        ORDER BY count DESC
    """
    return await execute_query(query)


# Fréquence des mots-clés dans les articles
@router.get("/keyword-frequency", response_model=List[KeywordFrequencyMetrics])
async def get_keyword_frequency(user=Depends(jwt_required)):
    return await get_keyword_frequency_generic("articles")


# Fréquence des mots-clés dans les articles scientifiques
@router.get("/scientific-keyword-frequency", response_model=List[KeywordFrequencyMetrics])
async def get_scientific_keyword_frequency(user=Depends(jwt_required)):
    return await get_keyword_frequency_generic("scientific_articles")


# Nombre de vidéos par source
@router.get("/videos-by-source", response_model=List[SourceMetrics])
async def get_videos_by_source(user=Depends(jwt_required)):
    query = """
        SELECT source, COUNT(*) as count
        FROM videos
        GROUP BY source
        ORDER BY count DESC
    """
    return await execute_query(query)


# Fonction générique pour la fréquence des mots-clés
async def get_keyword_frequency_generic(table_name: str) -> List[Dict[str, Any]]:
    query = f"""
        SELECT keyword, COUNT(*) as count
        FROM (
            SELECT TRIM(REGEXP_SUBSTR(keywords, '[^;]+', 1, n)) AS keyword
            FROM {table_name}
            JOIN (SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) numbers
            ON CHAR_LENGTH(keywords) - CHAR_LENGTH(REPLACE(keywords, ';', '')) >= n - 1
        ) AS exploded_keywords
        WHERE keyword IS NOT NULL
        GROUP BY keyword
        ORDER BY count DESC
    """
    return await execute_query(query)


# Fonction générique pour exécuter une requête SQL
async def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.commit()
        connection.close()

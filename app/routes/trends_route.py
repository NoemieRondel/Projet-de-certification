from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from datetime import datetime, timedelta
from app.security.jwt_handler import jwt_required
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()

# Modèle de réponse pour la liste des mots-clés tendance
class TrendingKeyword(BaseModel):
    keyword: str
    count: int


@router.get(
    "/keywords",
    summary="Récupère les mots-clés tendances",
    response_model=Dict[str, List[TrendingKeyword]],
    responses={
        200: {"description": "Succès"},
        400: {"description": "Paramètres de date invalides"},
        500: {"description": "Erreur interne"}
    }
)
async def get_trending_keywords(
    start_date: str = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Date de fin (YYYY-MM-DD)"),
    last_days: int = Query(None, description="Nombre de jours avant aujourd'hui"),
    limit: int = Query(50, description="Nombre de mots-clés à récupérer"),
    offset: int = Query(0, description="Offset pour la pagination"),
    user=Depends(jwt_required)  # Vérification du JWT
):
    """Retourne les mots-clés les plus fréquents sur une période donnée avec pagination."""

    # Détermination de la plage de dates
    start_dt, end_dt = determine_date_range(start_date, end_date, last_days)

    # Requête SQL optimisée
    query = """
        SELECT keyword, COUNT(*) as count 
        FROM (
            SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(keywords, ';', numbers.n), ';', -1)) AS keyword
            FROM articles 
            JOIN (SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL 
                  SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL 
                  SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10) numbers 
            ON CHAR_LENGTH(keywords) - CHAR_LENGTH(REPLACE(keywords, ';', '')) >= numbers.n - 1
            WHERE publication_date BETWEEN %s AND %s
        ) AS extracted_keywords
        WHERE keyword != ''
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT %s OFFSET %s;
    """

    # Exécution de la requête et retour des résultats
    result = await execute_query(query, (start_dt, end_dt, limit, offset))
    return {"trending_keywords": result}


def determine_date_range(start_date: str, end_date: str, last_days: int):
    """Calcule la plage de dates en fonction des paramètres fournis."""
    try:
        if last_days is not None:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=last_days)
        elif start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            raise ValueError("Paramètres de date manquants.")

        if start_dt > end_dt:
            raise ValueError("La date de début doit être antérieure à la date de fin.")

        return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def execute_query(query: str, params: tuple) -> List[Dict]:
    """Exécute une requête SQL et retourne le résultat sous forme de liste de dictionnaires."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur SQL : {str(e)}")

    finally:
        connection.close()

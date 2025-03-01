from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from datetime import datetime, timedelta
from app.security.jwt_handler import jwt_required
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()


# Modèle de réponse
class TrendingKeyword(BaseModel):
    keyword: str
    count: int


# Tendances des mots-clés avec pagination
@router.get(
    "/keywords",
    summary="Tendances des mots-clés",
    response_model=Dict[str, List[TrendingKeyword]],
    responses={
        200: {"description": "Mots-clés tendances récupérés avec succès."},
        400: {"description": "Paramètres de date invalides."},
        500: {"description": "Erreur interne."}
    }
)
async def get_trending_keywords(
    start_date: str = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Date de fin (YYYY-MM-DD)"),
    last_days: int = Query(None, description="Nombre de jours avant aujourd'hui"),
    limit: int = Query(10, description="Nombre de mots-clés à récupérer"),
    offset: int = Query(0, description="Offset pour la pagination"),
    user=Depends(jwt_required)  # Protection avec JWT
):
    """Retourne les mots-clés les plus fréquents sur une période donnée avec pagination."""

    # Détermination de la plage de dates
    start_dt, end_dt = determine_date_range(start_date, end_date, last_days)

    # Requête SQL optimisée avec REGEXP
    query = """
        SELECT keyword, COUNT(*) as count 
        FROM (
            SELECT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(keywords, ';', numbers.n), ';', -1)) AS keyword
            FROM articles 
            JOIN (SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL 
                  SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL 
                  SELECT 9 UNION ALL SELECT 10) numbers 
            ON CHAR_LENGTH(keywords) - CHAR_LENGTH(REPLACE(keywords, ';', '')) >= numbers.n - 1
            WHERE created_at BETWEEN %s AND %s
        ) AS extracted_keywords
        WHERE keyword != ''  -- Exclure les entrées vides
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT %s OFFSET %s;
    """

    # Exécution de la requête et retour des résultats
    result = await execute_query(query, (start_dt, end_dt, limit, offset))
    return {"trending_keywords": result}


# Fonction pour déterminer la plage de dates
def determine_date_range(start_date: str, end_date: str, last_days: int):
    """Calcule la plage de dates en fonction des paramètres fournis."""
    if last_days is not None:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=last_days)
    elif start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD.")
    else:
        raise HTTPException(status_code=400, detail="Veuillez fournir `last_days` ou une plage `start_date` - `end_date`.")

    if start_dt > end_dt:
        raise HTTPException(status_code=400, detail="La date de début doit être antérieure à la date de fin.")

    return start_dt, end_dt


# Fonction générique pour exécuter les requêtes
async def execute_query(query: str, params: tuple) -> List[Dict]:
    """Exécute une requête SQL et retourne le résultat sous forme de liste de dictionnaires."""
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
        connection.close()

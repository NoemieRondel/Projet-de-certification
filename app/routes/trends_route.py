from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from datetime import datetime, timedelta
from app.security.jwt_handler import jwt_required

router = APIRouter()


@router.get("/trends/keywords", summary="Tendances des mots-clés", description="Retourne les mots-clés les plus fréquents sur une période donnée.")
async def get_trending_keywords(
    start_date: str = Query(None, description="Date de début au format YYYY-MM-DD"),
    end_date: str = Query(None, description="Date de fin au format YYYY-MM-DD"),
    last_days: int = Query(None, description="Nombre de jours avant aujourd'hui"),
    user=Depends(jwt_required)  # Protection avec JWT
):
    """Retourne les tendances des mots-clés entre deux dates données ou sur une période dynamique."""

    # Déterminer la plage de dates
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

    # Requête SQL pour extraire les tendances en gérant les mots-clés multiples
    query = """
        WITH exploded AS (
            SELECT TRIM(value) AS keyword
            FROM articles, JSON_TABLE(
                REPLACE(CONCAT('["', REPLACE(keywords, ';', '","'), '"]'), ' ', '') 
                COLUMNS (value VARCHAR(255) PATH '$[*]')
            ) AS temp
            WHERE created_at BETWEEN %s AND %s
        )
        SELECT keyword, COUNT(*) as count
        FROM exploded
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 10;
    """

    # Connexion à la base de données
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, (start_dt, end_dt))
            result = cursor.fetchall()
            return {"trending_keywords": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        connection.close()

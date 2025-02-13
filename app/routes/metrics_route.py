from fastapi import APIRouter, HTTPException, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required  # Vérification JWT

router = APIRouter()


# Route pour récupérer le nombre d'articles par source
@router.get(
    "/metrics/articles-by-source",
    summary="Nombre d'articles par source",
    description="Retourne le nombre d'articles pour chaque source d'information."
)
async def get_articles_by_source(user=Depends(jwt_required)):  # Protection JWT
    """Récupère le nombre d'articles par source."""
    query = """
        SELECT source, COUNT(*) as count
        FROM articles
        GROUP BY source
    """
    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")


# Route pour récupérer la fréquence d'apparition des mots-clés
@router.get(
    "/metrics/keyword-frequency",
    summary="Fréquence des mots-clés",
    description="Retourne la fréquence d'apparition des mots-clés dans les articles."
)
async def get_keyword_frequency(user=Depends(jwt_required)):  # Protection JWT
    """Récupère la fréquence d'apparition des mots-clés."""
    query = """
        SELECT keywords, COUNT(*) as count
        FROM articles
        GROUP BY keywords
    """
    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")


# Route pour récupérer la distribution des publications par période
@router.get(
    "/metrics/publications-by-period",
    summary="Distribution des publications par période",
    description="Retourne la distribution des publications par date."
)
async def get_publications_by_period(user=Depends(jwt_required)):  # Protection JWT
    """Récupère la distribution des publications par période."""
    query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM articles
        GROUP BY DATE(created_at)
    """
    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# Modèle de réponse optimisé
class ArticleResponse(BaseModel):
    id: int
    title: str
    source: str
    publication_date: str
    keywords: Optional[str]
    summary: Optional[str]
    link: str


@router.get(
    "/",
    summary="Récupère tous les articles",
    response_model=List[ArticleResponse],  # Assure un formatage propre de la réponse
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
    user=Depends(jwt_required)  # Protection JWT
):
    """Récupère les articles avec filtres dynamiques."""

    query = """
        SELECT id, title, source, publication_date, keywords, summary, link
        FROM articles WHERE 1=1
    """
    params = []

    # Ajout des filtres dynamiquement
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

    # Connexion et exécution
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            articles = cursor.fetchall()

            if not articles:
                raise HTTPException(status_code=404, detail="Aucun article trouvé.")

            return articles

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


@router.get("/suggestions", summary="Obtenir les suggestions de sources et de mots-clés")
async def get_article_suggestions(user=Depends(jwt_required)):  # Protection JWT
    """Récupère les suggestions de sources et de mots-clés pour les articles."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            # Récupération des suggestions uniques pour les sources
            cursor.execute("SELECT DISTINCT source FROM articles WHERE source IS NOT NULL")
            sources = [row["source"] for row in cursor.fetchall()]

            # Récupération des suggestions uniques pour les mots-clés
            cursor.execute("SELECT DISTINCT keywords FROM articles WHERE keywords IS NOT NULL")
            keywords = set()
            for row in cursor.fetchall():
                keywords.update(row["keywords"].split(";"))  # Séparateur : `;`

            return {"sources": sources, "keywords": sorted(keywords)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()

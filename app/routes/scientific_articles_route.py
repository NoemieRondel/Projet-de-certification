from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# Modèle de réponse pour les articles scientifiques
class ScientificArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    authors: Optional[str]
    publication_date: str
    keywords: Optional[str]


# Route pour récupérer tous les articles scientifiques avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère tous les articles scientifiques avec filtres dynamiques",
    response_model=List[ScientificArticleResponse],  # Structure propre de la sortie
    responses={
        200: {"description": "Liste des articles scientifiques récupérés."},
        404: {"description": "Aucun article scientifique trouvé."},
        500: {"description": "Erreur interne."}
    }
)
async def get_all_scientific_articles(
    start_date: str = Query(None, description="Filtrer les articles à partir de cette date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Filtrer les articles jusqu'à cette date (YYYY-MM-DD)"),
    authors: str = Query(None, description="Filtrer par auteur(s) (séparés par des virgules)"),
    keywords: str = Query(None, description="Filtrer par mots-clés (séparés par des virgules)"),
    user=Depends(jwt_required)  # Protection avec JWT
):
    """Récupère les articles scientifiques avec filtres dynamiques."""
    query = """
        SELECT id, title, url, authors, publication_date, keywords
        FROM scientific_articles
        WHERE 1=1
    """
    params = []

    # Ajout des filtres dynamiquement
    if start_date:
        query += " AND publication_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND publication_date <= %s"
        params.append(end_date)

    if authors:
        author_list = [f"%{author.strip()}%" for author in authors.split(',')]
        query += " AND (" + " OR ".join(["authors LIKE %s"] * len(author_list)) + ")"
        params.extend(author_list)

    if keywords:
        keyword_list = [f"%{kw.strip()}%" for kw in keywords.split(',')]
        query += " AND (" + " OR ".join(["keywords LIKE %s"] * len(keyword_list)) + ")"
        params.extend(keyword_list)

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            articles = cursor.fetchall()

            if not articles:
                raise HTTPException(status_code=404, detail="Aucun article scientifique trouvé.")

            return articles

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


# Route pour récupérer les 10 derniers articles scientifiques publiés
@router.get(
    "/latest",
    summary="Derniers articles scientifiques publiés",
    response_model=List[ScientificArticleResponse],  # Structure propre de la sortie
    responses={
        200: {"description": "Liste des 10 derniers articles scientifiques."},
        500: {"description": "Erreur interne."}
    }
)
async def get_latest_scientific_articles(user=Depends(jwt_required)):  
    """Retourne les 10 derniers articles scientifiques publiés."""
    query = """
        SELECT id, title, url, authors, publication_date, keywords
        FROM scientific_articles
        ORDER BY publication_date DESC
        LIMIT 10
    """

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query)
            latest_articles = cursor.fetchall()

            if not latest_articles:
                raise HTTPException(status_code=404, detail="Aucun article scientifique trouvé.")

            return latest_articles

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()


# Route pour récupérer les suggestions d’auteurs et de mots-clés
@router.get(
    "/suggestions",
    summary="Suggestions d’auteurs et de mots-clés",
    responses={
        200: {"description": "Suggestions récupérées."},
        500: {"description": "Erreur interne."}
    }
)
async def get_suggestions_scientific_articles(user=Depends(jwt_required)):  
    """Retourne les suggestions d’auteurs et de mots-clés."""
    suggestions = {
        "authors": [],
        "keywords": []
    }

    query_authors = "SELECT DISTINCT authors FROM scientific_articles WHERE authors IS NOT NULL"
    query_keywords = "SELECT DISTINCT keywords FROM scientific_articles WHERE keywords IS NOT NULL"

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            # Récupérer les suggestions d’auteurs
            cursor.execute(query_authors)
            author_results = cursor.fetchall()
            suggestions["authors"] = [entry["authors"] for entry in author_results if entry["authors"]]

            # Récupérer les suggestions de mots-clés
            cursor.execute(query_keywords)
            keyword_results = cursor.fetchall()
            suggestions["keywords"] = [entry["keywords"] for entry in keyword_results if entry["keywords"]]

        return {"data": suggestions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        connection.close()

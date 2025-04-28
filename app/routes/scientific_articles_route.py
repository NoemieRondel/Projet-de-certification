from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import get_connection
from contextlib import closing
from app.security.jwt_handler import jwt_required
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter()


# Modèle de réponse pour les articles scientifiques
class ScientificArticleResponse(BaseModel):
    id: int
    title: str
    article_url: str
    authors: Optional[str]
    publication_date: str  # Publication date as string
    keywords: Optional[str]
    abstract: Optional[str]


# Fonction de validation de date
def validate_date(date_str):
    try:
        # Vérifie et convertit la date au format YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Format de date invalide : {date_str}. Utilisez YYYY-MM-DD.")


# Route pour récupérer tous les articles scientifiques avec filtres dynamiques
@router.get(
    "/",
    summary="Récupère tous les articles scientifiques avec filtres dynamiques",
    response_model=List[ScientificArticleResponse],
    responses={
        200: {"description": "Liste des articles scientifiques récupérés."},
        404: {"description": "Aucun article scientifique trouvé."},
        500: {"description": "Erreur interne."}
    }
)
async def get_all_scientific_articles(
    start_date: Optional[str] = Query(None, description="Filtrer les articles à partir de cette date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filtrer les articles jusqu'à cette date (YYYY-MM-DD)"),
    authors: Optional[str] = Query(None, description="Filtrer par auteur(s) (séparés par des virgules)"),
    keywords: Optional[str] = Query(None, description="Filtrer par mots-clés (séparés par des virgules)"),
    user=Depends(jwt_required)  # Dépendance pour vérifier le token JWT
):
    """Récupère les articles scientifiques avec filtres dynamiques."""
    query = """
        SELECT id, title, article_url, authors, publication_date, keywords, abstract
        FROM scientific_articles
        WHERE 1=1
    """
    params = []

    # Appliquer les filtres de manière dynamique
    if start_date:
        start_date = validate_date(start_date)  # Valider la date
        query += " AND publication_date >= %s"
        params.append(start_date)

    if end_date:
        end_date = validate_date(end_date)  # Valider la date
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

    # Ajout du tri par date (du plus récent au plus ancien)
    query += " ORDER BY publication_date DESC"

    # LOG : Requête SQL générée
    print(f"Requête SQL : {query}")
    print(f"Paramètres : {params}")

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            articles = cursor.fetchall()

            # LOG : Articles récupérés
            print(f"Articles récupérés : {articles}")

            if not articles:
                raise HTTPException(status_code=404, detail="Aucun article scientifique trouvé.")

            # Convertir publication_date en chaîne avant de renvoyer la réponse
            for article in articles:
                article['publication_date'] = article['publication_date'].strftime('%Y-%m-%d')

            # Retourner la liste des articles en réponse
            return articles

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# Route pour récupérer les 5 articles scientifiques les plus récents
@router.get(
    "/latest",
    summary="Récupère les 5 articles scientifiques les plus récents",
    response_model=List[ScientificArticleResponse],
    responses={
        200: {"description": "Liste des 5 articles scientifiques récupérés."},
        404: {"description": "Aucun article scientifique trouvé."},
        500: {"description": "Erreur interne."}
    }
)
async def get_latest_scientific_articles(
    user=Depends(jwt_required)  # Dépendance pour vérifier le token JWT
):
    """Récupère les 5 articles scientifiques les plus récents."""
    query = """
        SELECT id, title, article_url, authors, publication_date, keywords, abstract
        FROM scientific_articles
        ORDER BY publication_date DESC
        LIMIT 5
    """
    params = []

    # LOG : Requête SQL générée
    print(f"Requête SQL : {query}")
    print(f"Paramètres : {params}")

    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

    try:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, params)
            articles = cursor.fetchall()

            # LOG : Articles récupérés
            print(f"Articles récupérés : {articles}")

            if not articles:
                raise HTTPException(status_code=404, detail="Aucun article scientifique trouvé.")

            # Convertir publication_date en chaîne avant de renvoyer la réponse
            for article in articles:
                article['publication_date'] = article['publication_date'].strftime('%Y-%m-%d')

            # Retourner la liste des articles en réponse
            return articles

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de la requête : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

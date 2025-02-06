from fastapi import APIRouter, HTTPException, Query
from app.database import get_connection
from contextlib import closing

router = APIRouter()


@router.get(
    "/",
    summary="Récupère tous les articles scientifiques avec filtres dynamiques",
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
    keywords: str = Query(None, description="Filtrer par mots-clés (séparés par des virgules)")
):
    """Récupère les articles scientifiques avec filtres dynamiques."""
    query = "SELECT * FROM scientific_articles WHERE 1=1"
    params = []

    # Ajout des filtres dynamiques
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
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                cursor.execute(query, params)
                articles = cursor.fetchall()

                if not articles:
                    raise HTTPException(status_code=404, detail="Aucun article scientifique trouvé.")

                return {"data": articles}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

        finally:
            connection.close()
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")


@router.get(
    "/suggestions",
    summary="Suggestions pour les filtres auteurs et mots-clés",
    responses={
        200: {"description": "Suggestions récupérées."},
        500: {"description": "Erreur interne."}
    }
)
async def get_suggestions_scientific_articles():
    """Retourne les suggestions pour les auteurs et les mots-clés."""
    suggestions = {
        "authors": [],
        "keywords": []
    }

    query_authors = "SELECT DISTINCT authors FROM scientific_articles"
    query_keywords = "SELECT DISTINCT keywords FROM scientific_articles"

    connection = get_connection()
    if connection:
        try:
            with closing(connection.cursor(dictionary=True)) as cursor:
                # Récupérer les suggestions d'auteurs
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
    else:
        raise HTTPException(status_code=500, detail="Impossible de se connecter à la base de données.")

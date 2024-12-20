import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def fetch_venturebeat_content(url):
    """
    Récupère le contenu principal d'un article VentureBeat.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # VentureBeat : Contenu principal de l'article
        article_body = soup.find("div", class_="article-content")

        if not article_body:
            print(f"Impossible de trouver le contenu principal pour : {url}")
            return None

        # Extraire le texte
        content = article_body.get_text(separator=" ").strip()
        return content
    except Exception as e:
        print(f"Erreur lors de la récupération du contenu pour {url} : {e}")
        return None


def store_article_content(article_id, content):
    """
    Insère le contenu complet d'un article dans article_content
    uniquement s'il n'existe pas déjà.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Vérifier si l'article existe déjà dans la table
        cursor.execute("SELECT id FROM article_content WHERE article_id = %s",
                       (article_id,))
        result = cursor.fetchone()

        if result:
            print(f"L'article {article_id} est déjà présent dans la base.")
        else:
            # Insérer si pas encore présent
            cursor.execute(
                "INSERT INTO article_content (article_id, content) VALUES (%s, %s)",
                (article_id, content)
            )
            connection.commit()
            print(f"Contenu de l'article {article_id} enregistré avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du contenu de l'article {article_id} : {e}")
    finally:
        cursor.close()
        connection.close()


def main():
    """
    Script principal pour récupérer et stocker le contenu des articles VentureBeat.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sélectionner les articles VentureBeat dans la table articles
        cursor.execute("SELECT id, link FROM articles WHERE source = 'VentureBeat'")
        articles = cursor.fetchall()

        for article in articles:
            article_id = article["id"]
            url = article["link"]

            print(f"Traitement de l'article {article_id} ({url})...")

            # Récupérer le contenu
            content = fetch_venturebeat_content(url)
            if not content:
                print(f"Impossible de récupérer le contenu pour l'URL : {url}")
                continue

            # Enregistrer le contenu dans la table article_content
            store_article_content(article_id, content)

        print("Traitement terminé.")
    except Exception as e:
        print(f"Erreur dans le script principal : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()

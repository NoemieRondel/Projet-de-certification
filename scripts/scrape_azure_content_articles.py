import os
import time
import mysql.connector
import requests
from bs4 import BeautifulSoup
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

def fetch_azure_blog_content_with_beautifulsoup(url):
    """Récupérer et parser le contenu d'un article Azure Blog en utilisant BeautifulSoup."""
    try:
        # Récupérer le contenu de la page avec requests
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Erreur de récupération de l'article {url} (Code HTTP: {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Rechercher le contenu principal
        main_content = soup.find("article") # Tentative de structure
        if not main_content:
            main_content = soup.find("main")  # Autre tentative

        if not main_content:
            print(f"Aucun contenu trouvé pour l'URL {url}. Vérifie la structure de la page.")
            return None

        # Extraire les paragraphes et autres éléments pour l'article complet
        content = []
        for p in main_content.find_all("p"):
            if p.get_text(strip=True):
                content.append(p.get_text(strip=True))

        for h2 in main_content.find_all("h2"):
            if h2.get_text(strip=True):
                content.append(h2.get_text(strip=True))
        
        for h3 in main_content.find_all("h3"):
            if h3.get_text(strip=True):
                content.append(h3.get_text(strip=True))

        if not content:
            print(f"Aucun contenu textuel trouvé pour l'URL {url}.")
            return None

        return "\n".join(content)

    except Exception as e:
        print(f"Erreur lors de la récupération de l'article {url} : {e}")
        return None

def store_article_content(article_id, content):
    """Enregistrer le contenu de l'article dans la base de données."""
    if content is None:
        print(f"Aucun contenu pour l'article {article_id}, rien à enregistrer.")
        return

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Vérifier si l'article existe déjà
        cursor.execute("SELECT id FROM article_content WHERE article_id = %s", (article_id,))
        result = cursor.fetchone()

        if result:
            print(f"L'article {article_id} est déjà présent dans la base.")
        else:
            # Insérer le contenu de l'article
            cursor.execute(
                "INSERT INTO article_content (article_id, content) VALUES (%s, %s)",
                (article_id, content)
            )
            connection.commit()
            print(f"Contenu de l'article {article_id} enregistré avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du contenu de l'article {article_id} : {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

def main():
    """Script principal pour récupérer et stocker le contenu des articles Azure Blog."""
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Récupérer les articles à traiter
        cursor.execute("SELECT id, link FROM articles WHERE source = 'Azure Blog'")
        articles = cursor.fetchall()

        for article in articles:
            article_id = article["id"]
            url = article["link"]
            print(f"Traitement de l'article {article_id} ({url})...")

            content = fetch_azure_blog_content_with_beautifulsoup(url)
            if not content:
                print(f"Impossible de récupérer le contenu pour l'URL : {url}")
                continue

            store_article_content(article_id, content)
            time.sleep(2)  # Pause pour éviter les requêtes rapides

        print("Traitement terminé.")
    except Exception as e:
        print(f"Erreur dans le script principal : {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    main()

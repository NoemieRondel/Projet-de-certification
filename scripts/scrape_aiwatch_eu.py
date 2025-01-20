import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import time

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# URL du flux RSS
RSS_URL = "https://ai-watch.ec.europa.eu/node/2/rss_en"


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def save_to_db(article_data):
    """
    Enregistre ou met à jour les données d'un article dans la base de données.
    """
    query = """
        INSERT INTO articles (
            title,
            source,
            publication_date,
            link,
            author,
            summary,
            full_content,
            language
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            source = VALUES(source),
            publication_date = VALUES(publication_date),
            author = VALUES(author),
            summary = VALUES(summary),
            full_content = VALUES(full_content),
            language = VALUES(language);
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (
            article_data["title"],
            article_data["source"],
            article_data["publication_date"],
            article_data["link"],
            article_data["author"],
            article_data["summary"],
            article_data["full_content"],
            article_data["language"],
        ))
        conn.commit()
        print(f"Article inséré/mis à jour : {article_data['title']}")
    except mysql.connector.Error as err:
        print(f"Erreur MySQL : {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def fetch_full_content(url):
    """
    Récupère le contenu complet d'un article à partir de son URL.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 429:  # Trop de requêtes
            print("Trop de requêtes ! Pause de 60 secondes.")
            time.sleep(60)
            return fetch_full_content(url)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_body = soup.find("article")

        if not article_body:
            print(f"Aucun contenu trouvé pour l'URL {url}.")
            return None

        paragraphs = [p.get_text(strip=True) for p in article_body.find_all("p")]
        return "\n".join(paragraphs) if paragraphs else None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du contenu de l'article {url} : {e}")
        return None


def scrape_rss_feed():
    """
    Scrape les articles à partir du flux RSS.
    """
    try:
        response = requests.get(RSS_URL)
        if response.status_code != 200:
            print(f"Erreur HTTP : {response.status_code}")
            return

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        for item in items:
            title = item.find("title").text.strip() if item.find("title") else "No title"
            link = item.find("link").text.strip() if item.find("link") else None
            summary = item.find("description").text.strip() if item.find("description") else "No summary available."
            if summary != "No summary available.":
                summary = BeautifulSoup(summary, "html.parser").get_text().strip()

            pub_date = item.find("pubDate").text.strip() if item.find("pubDate") else None
            if pub_date:
                try:
                    pub_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
                except ValueError as e:
                    print(f"Erreur lors de la conversion de la date : {e}")
                    pub_date = None

            # Champs fixes
            source = "AI Watch European Commission"
            author = "AI Watch"
            language = "english"

            # Récupérer le contenu complet de l'article
            full_content = fetch_full_content(link)

            # Préparer les données de l'article
            article_data = {
                "title": title,
                "source": source,
                "publication_date": pub_date,
                "link": link,
                "author": author,
                "summary": summary,
                "full_content": full_content,
                "language": language,
            }

            # Sauvegarder dans la base de données
            save_to_db(article_data)
            time.sleep(2)  # Pause pour éviter trop de requêtes rapides
    except Exception as e:
        print(f"Erreur lors du scraping du flux RSS : {e}")


if __name__ == "__main__":
    # Lancer le scraping
    scrape_rss_feed()

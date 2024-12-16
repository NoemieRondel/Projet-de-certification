import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv
import os

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


def save_to_db(article_data):
    """
    Enregistre ou met à jour les données d'un article dans la base de données.
    """
    query_insert = """
        INSERT INTO articles (
            title,
            source,
            publication_date,
            link,
            author,
            content,
            language)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        source = VALUES(source),
        publication_date = VALUES(publication_date),
        author = VALUES(author),
        content = VALUES(content),
        language = VALUES(language);
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query_insert, (
            article_data["title"],
            article_data["source"],
            article_data["publication_date"],
            article_data["link"],
            article_data["author"],
            article_data["content"],
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


def scrape_rss_feed(url):
    """
    Scrape les articles à partir du flux RSS spécifié.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur HTTP : {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "xml")
    items = soup.find_all("item")

    for item in items:
        # Extraction des informations
        title = item.find(
            "title").text.strip() if item.find("title") else "No title"
        link = item.find("link").text.strip() if item.find("link") else None
        description = item.find(
            "description").text.strip() if item.find(
                "description") else "No description available."
        if description != "No description available.":
            description = BeautifulSoup(
                description,
                "html.parser").get_text().strip()

        pub_date = item.find("pubDate").text.strip() if item.find(
            "pubDate") else None
        if pub_date:
            try:
                # Conversion en format YYYY-MM-DD
                pub_date = datetime.strptime(
                    pub_date,
                    "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
            except ValueError as e:
                print(f"Erreur lors de la conversion de la date : {e}")
                pub_date = None

        # Champs fixes
        source = "AI Watch European Commission"
        author = "AI Watch"
        language = "english"

        # Structure des données
        article_data = {
            "title": title,
            "source": source,
            "publication_date": pub_date,
            "link": link,
            "author": author,
            "content": description,
            "language": language,
        }

        # Sauvegarder dans la base
        save_to_db(article_data)


if __name__ == "__main__":
    # Scraping du flux RSS
    scrape_rss_feed(RSS_URL)

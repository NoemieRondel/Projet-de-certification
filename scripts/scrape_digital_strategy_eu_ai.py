import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
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

# URL de base pour Digital Strategy
BASE_URL = "https://digital-strategy.ec.europa.eu"
PAGE_URL = "/en/related-content?topic=119"


def save_to_db(article_data):
    """
    Enregistre ou met à jour les données d'un article dans la base de données.
    """
    query_insert = """
        INSERT INTO articles (title, source, publication_date, link, author, content, language)
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


def extract_date(article):
    """
    Extrait et formate la date de publication de l'article.
    Si la date est vide ou mal formatée, renvoie None.
    """
    time_tag = article.find("time")
    if time_tag:
        date_str = time_tag.get("datetime").strip()

        if not date_str:
            print("Date vide pour cet article.")
            return None

        # Nettoyage si la date contient un suffixe ou préfixe comme " -"
        date_str = date_str.split(" -")[0]

        try:
            formatted_date = datetime.strptime(date_str, "%d %B %Y").strftime("%Y-%m-%d")
            return formatted_date
        except ValueError as e:
            print(f"Erreur lors de la conversion de la date : {e}")
            return None
    return None


def scrape_page(url):
    """
    Scrape les articles à partir de la page spécifiée.
    """
    response = requests.get(urljoin(BASE_URL, url))
    if response.status_code != 200:
        print(f"Erreur HTTP : {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="ecl-u-d-flex")

    for article in articles:
        # Extraction des informations
        title_tag = article.find("a", class_="ecl-link")
        title = title_tag.text.strip() if title_tag else "No title"
        link = urljoin(BASE_URL, title_tag["href"]) if title_tag else None

        date = extract_date(article)

        content_tag = article.find("div", class_="cnt-teaser")
        content = content_tag.text.strip() if content_tag else "No content available."

        # Champs fixes
        source = "Digital Strategy"
        author = "European Commission"
        language = "english"

        # Structure des données
        article_data = {
            "title": title,
            "source": source,
            "publication_date": date,
            "link": link,
            "author": author,
            "content": content,
            "language": language,
        }

        # Sauvegarder dans la base
        save_to_db(article_data)


if __name__ == "__main__":
    # Scraping de la page principale
    scrape_page(PAGE_URL)

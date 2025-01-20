import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import mysql.connector
from dotenv import load_dotenv

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


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


def save_to_db(article_data):
    """
    Enregistre ou met à jour les données d'un article dans la base de données.
    """
    query_insert = """
        INSERT INTO articles (title, source, publication_date, link, author, full_content, summary, language)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        source = VALUES(source),
        publication_date = VALUES(publication_date),
        author = VALUES(author),
        full_content = VALUES(full_content),
        summary = VALUES(summary),
        language = VALUES(language);
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query_insert, (
            article_data["title"],
            article_data["source"],
            article_data["publication_date"],
            article_data["link"],
            article_data["author"],
            article_data["full_content"],
            article_data["summary"],
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
        date_str = time_tag.get("datetime", "").strip()

        if not date_str:
            print("Date vide pour cet article.")
            return None

        try:
            # Essayez plusieurs formats de date
            for fmt in ("%d %B %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            print(f"Format de date non pris en charge : {date_str}")
            return None
        except Exception as e:
            print(f"Erreur lors de la conversion de la date : {e}")
            return None
    return None


def fetch_digital_strategy_content(url):
    """
    Récupérer et parser le contenu complet d'un article Digital Strategy.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            print("Trop de requêtes ! Pause de 60 secondes.")
            time.sleep(60)
            return fetch_digital_strategy_content(url)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        main_content = soup.find("div", class_="cnt-main-body")

        if main_content:
            paragraphs = [p.get_text(strip=True) for p in main_content.find_all("p")]
            return "\n".join(paragraphs)
        else:
            print(f"Aucun contenu trouvé pour l'URL {url}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'article {url} : {e}")
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
        title_tag = article.find("a", class_="ecl-link")
        title = title_tag.text.strip() if title_tag else "No title"
        link = urljoin(BASE_URL, title_tag["href"]) if title_tag else None

        publication_date = extract_date(article)

        summary_tag = article.find("div", class_="cnt-teaser")
        summary = summary_tag.text.strip() if summary_tag else "No summary available."

        # Récupérer le contenu complet
        full_content = fetch_digital_strategy_content(link) if link else None

        # Champs fixes
        source = "Digital Strategy"
        author = "European Commission"
        language = "english"

        # Structure des données
        article_data = {
            "title": title,
            "source": source,
            "publication_date": publication_date,
            "link": link,
            "author": author,
            "full_content": full_content,
            "summary": summary,
            "language": language,
        }

        # Sauvegarder dans la base
        save_to_db(article_data)
        time.sleep(2)  # Pause pour éviter de surcharger le serveur


if __name__ == "__main__":
    scrape_page(PAGE_URL)

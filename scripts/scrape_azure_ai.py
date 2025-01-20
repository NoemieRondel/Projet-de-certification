import mysql.connector
import feedparser
import requests
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
import time

# Charger les variables d'environnement
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# Connexion à la base de données
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("Connexion réussie à la base de données.")
        return connection
    except mysql.connector.Error as err:
        print(f"Erreur de connexion : {err}")
        return None


# Valider et formater la date
def validate_and_format_date(date_str):
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return date_obj.date()
    except ValueError:
        return None


# Nettoyer le contenu HTML
def clean_html_content(content):
    soup = BeautifulSoup(content, "lxml")
    return soup.get_text()


# Récupérer le contenu complet de l'article avec BeautifulSoup
def fetch_full_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Erreur HTTP {response.status_code} pour l'URL : {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        main_content = soup.find("article") or soup.find("main")
        if not main_content:
            print(f"Impossible de trouver le contenu principal pour {url}")
            return None

        content = []
        for tag in ["p", "h2", "h3"]:
            for element in main_content.find_all(tag):
                text = element.get_text(strip=True)
                if text:
                    content.append(text)

        return "\n".join(content) if content else None
    except Exception as e:
        print(f"Erreur lors de l'extraction du contenu complet : {e}")
        return None


# Traiter chaque flux RSS
def process_feed(feed_url, connection):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        # Ajout du User-Agent
        response = requests.get(feed_url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"Erreur HTTP {response.status_code} pour le flux RSS : {feed_url}")
            return

        feed = feedparser.parse(response.content)
        cursor = connection.cursor()

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            author = entry.get("author", "Unknown")
            summary = clean_html_content(entry.get("summary", "No summary available"))
            publication_date = validate_and_format_date(entry.get("published"))
            full_content = fetch_full_content(link)

            # Vérifier si l'article existe déjà
            cursor.execute("SELECT COUNT(*) FROM articles WHERE link = %s", (link,))
            article_exists = cursor.fetchone()[0] > 0

            if article_exists:
                print(f"L'article '{title}' existe déjà. Mise à jour...")
                update_query = """
                    UPDATE articles
                    SET title = %s, source = %s, publication_date = %s,
                        summary = %s, full_content = %s, language = %s, author = %s
                    WHERE link = %s
                """
                cursor.execute(update_query, (
                    title, "Azure Blog", publication_date, summary,
                    full_content, "english", author, link
                ))
            else:
                print(f"Insertion de l'article '{title}' dans la base de données...")
                insert_query = """
                    INSERT INTO articles (title, source, publication_date, summary, 
                        full_content, language, link, author)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    title, "Azure Blog", publication_date, summary,
                    full_content, "english", link, author
                ))

            # Pause pour éviter le blocage
            time.sleep(1)

        connection.commit()
        print(f"Traitement du flux : {feed_url} terminé.")
        cursor.close()
    except Exception as e:
        print(f"Erreur lors du traitement du flux {feed_url} : {e}")


# Script principal
def main():
    connection = connect_to_database()
    if connection is None:
        return

    # Liste des flux RSS à traiter (uniquement Azure Blog)
    feeds = [
        "https://azure.microsoft.com/en-us/blog/feed/"
    ]

    for feed_url in feeds:
        print(f"Traitement du flux : {feed_url}...")
        process_feed(feed_url, connection)

    connection.close()


if __name__ == "__main__":
    main()

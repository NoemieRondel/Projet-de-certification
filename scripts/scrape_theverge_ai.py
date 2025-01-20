import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
import feedparser
from datetime import datetime
from dotenv import load_dotenv
import re

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# URL du flux RSS
RSS_URL = "https://www.theverge.com/rss/index.xml"

# Mots-clés pour filtrer les articles pertinents
KEYWORDS = ["AI", "artificial intelligence", "machine learning", "neural networks", "deep learning"]


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def is_relevant(entry):
    """Vérifie si l'article est pertinent en fonction des mots-clés."""
    title = entry.get("title", "").lower()
    summary = entry.get("summary", "").lower()
    return any(keyword.lower() in title or keyword.lower() in summary for keyword in KEYWORDS)


def clean_content(content):
    """Nettoie le contenu HTML pour obtenir du texte brut."""
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    # Supprimer les balises inutiles
    for tag in soup(["script", "style", "figure"]):
        tag.decompose()
    # Obtenir le texte brut
    text = soup.get_text(separator="\n").strip()
    # Supprimer les espaces multiples
    text = re.sub(r"\s+", " ", text)
    return text


def fetch_theverge_content(url):
    """Récupère le contenu complet de l'article à partir de son URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Localiser les sections contenant le contenu de l'article
        article_sections = soup.find_all("div", class_="duet--article--article-body-component")

        content = []
        for section in article_sections:
            paragraphs = section.find_all("p", class_="duet--article--dangerously-set-cms-markup")
            for paragraph in paragraphs:
                content.append(paragraph.get_text(strip=True))

        return clean_content("\n".join(content)) if content else "Aucun contenu trouvé."
    except requests.exceptions.RequestException as e:
        return f"Error fetching content: {e}"


def fetch_articles():
    """Récupère les articles pertinents depuis le flux RSS."""
    print("Récupération d'articles à partir du flux RSS The Verge...")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("Aucun article récupéré. Vérifiez l'URL du flux RSS.")
        return []

    articles = []
    for entry in feed.entries:
        title = entry.get("title", "None")
        link = entry.get("link", "")
        published_raw = entry.get("published", "")
        summary = entry.get("summary", "No summary provided")  # Extraction du summary
        author = entry.get("author", "Unknown")

        # Conversion et nettoyage de la date
        published_date = None
        try:
            published_date = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%S%z").date()
        except (ValueError, TypeError):
            print(f"Date de publication invalide: {published_raw}")

        # Vérification de la pertinence
        if is_relevant(entry):
            full_content = fetch_theverge_content(link)  # Récupération du contenu complet
            articles.append({
                "title": title,
                "link": link,
                "published_date": published_date,
                "summary": clean_content(summary),  # Nettoyage du summary si nécessaire
                "full_content": full_content,
                "language": "english",
                "source": "The Verge",
                "author": author
            })

    print(f"{len(articles)} articles pertinents récupérés.")
    return articles


def insert_articles_to_db(articles):
    """Insère ou met à jour les articles dans la base de données."""
    print("Insertion des articles dans la base de données...")

    connection = None
    try:
        connection = connect_db()
        cursor = connection.cursor()

        for article in articles:
            try:
                # Requête d'insertion avec mise à jour
                query = """
                INSERT INTO articles (title, link, publication_date, summary, full_content, language, source, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                summary = VALUES(summary),
                full_content = VALUES(full_content),
                publication_date = VALUES(publication_date),
                source = VALUES(source),
                author = VALUES(author);
                """
                cursor.execute(query, (
                    article["title"],
                    article["link"],
                    article["published_date"],
                    article["summary"],
                    article["full_content"],
                    article["language"],
                    article["source"],
                    article["author"]
                ))
                connection.commit()
            except mysql.connector.Error as err:
                print(f"Erreur lors de l'insertion de l'article : {err}")
                print(f"Article data: {article}")

    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données : {err}")
    finally:
        if connection:
            connection.close()


def main():
    articles = fetch_articles()
    if articles:
        insert_articles_to_db(articles)
    else:
        print("Aucun article pertinent à insérer.")


if __name__ == "__main__":
    main()

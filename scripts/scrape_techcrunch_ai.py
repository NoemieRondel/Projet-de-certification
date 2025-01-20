import os
import mysql.connector
import feedparser
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re
import requests

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# URL du flux RSS
RSS_URL = "https://techcrunch.com/feed/"

# Mots-clés pour filtrer les articles pertinents
KEYWORDS = ["AI", "artificial intelligence", "machine learning",
            "neural networks", "deep learning"]


def is_relevant(entry):
    """Vérifie si l'article est pertinent en fonction des mots-clés."""
    title = entry.get("title", "").lower()
    content = entry.get("description", "")
    return any(keyword.lower() in title or keyword.lower() in content for keyword in KEYWORDS)


def clean_content(content):
    """Nettoie et simplifie le contenu HTML."""
    if not content:
        return ""

    soup = BeautifulSoup(content, "html.parser")
    # Supprimer les balises <script>, <style>, etc.
    for tag in soup(["script", "style", "figure"]):
        tag.decompose()
    # Récupérer le texte brut
    text = soup.get_text(separator="\n")
    # Supprimer les espaces multiples
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_full_content(url):
    """Récupère le contenu complet de l'article à partir de l'URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_section = soup.find("div", class_="entry-content")

        if not article_section:
            return "Aucun contenu trouvé ou structure HTML différente."

        content = []
        paragraphs = article_section.find_all("p")
        for paragraph in paragraphs:
            content.append(paragraph.get_text(strip=True))

        full_content = "\n".join(content)
        return full_content if full_content else "Aucun contenu pertinent trouvé."
    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la récupération de l'article : {e}"


def fetch_articles():
    """Récupère et traite les articles depuis le flux RSS."""
    print("Récupération des articles depuis TechCrunch...")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("Aucun article récupéré. Vérifiez l'URL du flux RSS.")
        return []

    articles = []
    for entry in feed.entries:
        title = entry.get("title", "None")
        link = entry.get("link", "")
        published_raw = entry.get("published", "")
        content = entry.get("content", [{}])[0].get("value", "")
        if not content:
            content = entry.get("description", "")

        # Extraction de l'auteur via dc:creator
        author = entry.get("dc:creator", None)
        if not author:
            author = entry.get("author", "Unknown")

        # Nettoyage et conversion des dates
        published_date = None
        try:
            published_date = datetime.strptime(published_raw, "%a, %d %b %Y %H:%M:%S %z").date()
        except (ValueError, TypeError):
            print(f"Date de publication invalide : {published_raw}")

        # Vérification de la pertinence
        if is_relevant(entry):
            full_content = fetch_full_content(link)  # Récupère le contenu
            articles.append({
                "title": title,
                "link": link,
                "published_date": published_date,
                "summary": clean_content(content),  # Résumé extrait
                "full_content": full_content,  # Contenu complet de l'article
                "language": "english",
                "source": "TechCrunch",
                "author": author
            })

    print(f"{len(articles)} articles pertinents récupérés.")
    return articles


def insert_articles_to_db(articles):
    """Insère ou met à jour les articles dans la base de données."""
    print("Insertion des articles dans la base de données...")

    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
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
                print(f"Données de l'article : {article}")

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

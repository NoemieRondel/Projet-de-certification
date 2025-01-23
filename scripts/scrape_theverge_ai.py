import os
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime
from dotenv import load_dotenv
import re
import json

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
KEYWORDS = ["AI", "artificial intelligence", "machine learning",
            "neural networks", "deep learning"]

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "theverge_articles.json")


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
        summary = entry.get("summary", "No summary available.")
        author = entry.get("author", "Unknown")

        # Conversion et nettoyage de la date
        published_date = None
        try:
            published_date = datetime.strptime(published_raw, "%Y-%m-%dT%H:%M:%S%z").date()
        except (ValueError, TypeError):
            print(f"Date de publication invalide: {published_raw}")

        # Vérification de la pertinence
        if is_relevant(entry):
            full_content = fetch_theverge_content(link)
            articles.append({
                "title": title,
                "link": link,
                "published_date": published_date,
                "summary": clean_content(summary),
                "full_content": full_content,
                "language": "english",
                "source": "The Verge",
                "author": author
            })

    print(f"{len(articles)} articles pertinents récupérés.")
    return articles


def save_articles_to_json(articles):
    """Sauvegarde les articles dans un fichier JSON."""
    print(f"Sauvegarde des articles dans le fichier JSON : {JSON_OUTPUT_FILE}")
    try:
        # Charger les articles existants s'il y en a
        if os.path.exists(JSON_OUTPUT_FILE):
            with open(JSON_OUTPUT_FILE, "r") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        # Indexer les articles existants par leurs liens pour éviter les doublons
        existing_links = {article["link"] for article in existing_data}

        # Ajouter uniquement les nouveaux articles
        new_articles = [article for article in articles if article["link"] not in existing_links]

        # Ajouter les nouveaux articles à la liste existante
        existing_data.extend(new_articles)

        # Écrire dans le fichier JSON
        with open(JSON_OUTPUT_FILE, "w") as file:
            json.dump(existing_data, file, indent=4, default=str)
        print(f"{len(new_articles)} articles nouveaux ont été sauvegardés avec succès dans le fichier JSON.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")


def main():
    articles = fetch_articles()
    if articles:
        save_articles_to_json(articles)  # Sauvegarde des articles dans un JSON
    else:
        print("Aucun article pertinent à sauvegarder.")


if __name__ == "__main__":
    main()

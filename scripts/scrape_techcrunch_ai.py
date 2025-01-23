import os
import json
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
import re
import requests

# URL du flux RSS
RSS_URL = "https://techcrunch.com/feed/"

# Mots-clés pour filtrer les articles pertinents
KEYWORDS = ["AI", "artificial intelligence", "machine learning",
            "neural networks", "deep learning"]

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "techcrunch_articles.json")


def load_existing_articles():
    """Charge les articles existants depuis le fichier JSON."""
    if os.path.exists(JSON_OUTPUT_FILE):
        with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_articles_to_json(articles):
    """Enregistre les articles dans un fichier JSON."""
    print(f"Enregistrement des articles dans le fichier JSON : {JSON_OUTPUT_FILE}")
    try:
        with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(articles, file, indent=4, ensure_ascii=False, default=str)
        print("Articles enregistrés avec succès dans le fichier JSON.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement dans le fichier JSON : {e}")


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


def main():
    # Charger les articles existants
    existing_articles = load_existing_articles()
    existing_links = {article["link"] for article in existing_articles}

    # Récupérer les nouveaux articles
    new_articles = fetch_articles()

    # Filtrer les articles déjà présents
    unique_articles = [article for article in new_articles if article["link"] not in existing_links]

    # Ajouter les nouveaux articles uniques à la liste existante
    existing_articles.extend(unique_articles)

    # Sauvegarder les articles combinés
    save_articles_to_json(existing_articles)

    print(f"Nombre d'articles ajoutés : {len(unique_articles)}")


if __name__ == "__main__":
    main()

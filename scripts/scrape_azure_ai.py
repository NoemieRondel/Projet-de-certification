import feedparser
import requests
import time
import os
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "azure_blog_articles.json")


# Nettoyer le contenu HTML
def clean_html_content(content):
    soup = BeautifulSoup(content, "lxml")
    return soup.get_text()


# Valider et formater la date
def validate_and_format_date(date_str):
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return date_obj.date()
    except ValueError:
        return None


# Récupérer le contenu complet de l'article avec BeautifulSoup
def fetch_full_content(url, retries=3, delay=5):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        for _ in range(retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"Erreur HTTP {response.status_code} pour l'URL : {url}")
                    return None
                soup = BeautifulSoup(response.text, 'html.parser')
                main_content = soup.find("article") or soup.find("main")
                if not main_content:
                    logger.warning(f"Impossible de trouver le contenu principal pour {url}")
                    return None
                content = []
                for tag in ["p", "h2", "h3"]:
                    for element in main_content.find_all(tag):
                        text = element.get_text(strip=True)
                        if text:
                            content.append(text)
                return "\n".join(content) if content else None
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout lors de la récupération du contenu de {url}. Nouvelle tentative...")
                time.sleep(delay)
        logger.error(f"Erreur lors de l'extraction du contenu après plusieurs tentatives : {url}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du contenu complet : {e}")
        return None


# Charger ou initialiser les données JSON
def load_json_data():
    if os.path.exists(JSON_OUTPUT_FILE):
        with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


# Sauvegarder les articles dans un fichier JSON
def save_to_json(data):
    try:
        existing_data = load_json_data()
        existing_links = {article["link"] for article in existing_data}

        # Ajouter uniquement les nouveaux articles
        new_articles = [item for item in data if item["link"] not in existing_links]
        existing_data.extend(new_articles)

        with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"{len(new_articles)} nouveaux articles ajoutés au fichier JSON.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde JSON : {e}")


# Traiter chaque flux RSS
def process_feed(feed_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        response = requests.get(feed_url, headers=headers, timeout=30)
        if response.status_code != 200:
            logger.error(f"Erreur HTTP {response.status_code} pour le flux RSS : {feed_url}")
            return

        feed = feedparser.parse(response.content)
        articles = []

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            author = entry.get("author", "Unknown")
            summary = clean_html_content(entry.get("summary", "No summary available."))
            publication_date = validate_and_format_date(entry.get("published"))
            full_content = fetch_full_content(link)

            article_data = {
                "title": title,
                "link": link,
                "author": author,
                "summary": summary,
                "publication_date": str(publication_date) if publication_date else None,
                "full_content": full_content,
                "source": "Azure Blog",
                "language": "english"
            }

            articles.append(article_data)

        # Enregistrer les articles dans le fichier JSON
        save_to_json(articles)
        logger.info(f"Traitement du flux RSS '{feed_url}' terminé.")

    except Exception as e:
        logger.error(f"Erreur lors du traitement du flux RSS : {e}")


# Fonction principale
def main():
    # Flux RSS pour le blog Azure
    azure_feed_url = "https://azure.microsoft.com/en-us/blog/feed/"
    process_feed(azure_feed_url)


if __name__ == "__main__":
    main()

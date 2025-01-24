import os
import json
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL du flux RSS
RSS_URL = "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/Category?category.id=AI"

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "techcommunity_articles.json")


# Fonction pour récupérer les articles depuis un flux RSS
def fetch_rss_articles(rss_url):
    logging.info(f"Récupération des articles depuis le flux RSS: {rss_url}")
    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        # Récupérer le résumé et le contenu brut
        raw_content = entry.description if 'description' in entry else None
        clean_content = clean_html(raw_content) if raw_content else None

        article = {
            "title": entry.title,
            "author": entry.author if 'author' in entry else None,
            "publication_date": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
            if 'published_parsed' in entry else None,
            "language": "english",
            "link": entry.link,
            "source": "Tech Community Microsoft",
            "full_content": clean_content
        }
        articles.append(article)

    logging.info(f"{len(articles)} articles récupérés.")
    return articles


# Fonction pour nettoyer le contenu HTML
def clean_html(html_content):
    logging.debug("Nettoyage du contenu HTML...")
    soup = BeautifulSoup(html_content, "html.parser")
    cleaned_content = soup.get_text(strip=True)
    return cleaned_content


# Fonction pour sauvegarder les articles en JSON avec dédoublonnage
def save_articles_to_json(articles, json_file):
    try:
        logging.info(f"Sauvegarde des articles dans le fichier JSON: {json_file}")

        # Charger les données existantes ou initialiser une liste vide
        existing_data = []
        if os.path.exists(json_file):
            with open(json_file, "r", encoding="utf-8") as file:
                existing_data = json.load(file)

        # Indexer les articles existants par leurs liens pour éviter les doublons
        existing_links = {article["link"] for article in existing_data}

        # Ajouter uniquement les nouveaux articles
        new_articles = [article for article in articles if article["link"] not in existing_links]
        existing_data.extend(new_articles)

        # Sauvegarder dans le fichier JSON
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)

        logging.info(f"{len(new_articles)} nouveaux articles ajoutés à {json_file}.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde des articles en JSON : {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        logging.info("Début du traitement des articles.")
        articles = fetch_rss_articles(RSS_URL)
        if articles:
            save_articles_to_json(articles, JSON_OUTPUT_FILE)
            logging.info("Les articles ont été traités avec succès.")
        else:
            logging.warning("Aucun article trouvé dans le flux RSS.")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution : {e}")

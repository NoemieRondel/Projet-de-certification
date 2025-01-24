import os
import json
import feedparser
import logging
from datetime import datetime

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL du flux RSS
RSS_URL = "https://www.technologyreview.com/feed/"

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "mit_articles.json")


# Fonction pour récupérer les articles depuis un flux RSS
def fetch_rss_articles(rss_url):
    logging.info(f"Récupération des articles depuis le flux RSS: {rss_url}")
    feed = feedparser.parse(rss_url)
    articles = []

    logging.info(f"Nombre d'articles trouvés dans le flux : {len(feed.entries)}")
    for entry in feed.entries:
        logging.debug("\n--- Article brut ---")
        logging.debug(entry)  # Affiche toutes les données de l'article pour inspection

        # Vérifier si la catégorie correspond à "Artificial Intelligence"
        if 'category' in entry:
            logging.info(f"Catégorie trouvée : {entry.category}")
            if entry.category == "Artificial intelligence":
                article = {
                    "title": entry.title,
                    "author": entry.author if 'author' in entry else None,
                    "publication_date": datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                    if 'published_parsed' in entry else None,
                    "language": "english",
                    "link": entry.link,
                    "source": "MIT Technology Review",
                    "full_content": entry.description if 'description' in entry else None
                }
                articles.append(article)
        else:
            logging.warning("Aucune catégorie trouvée pour cet article.")

    logging.info(f"Nombre d'articles filtrés : {len(articles)}")
    return articles


# Fonction pour sauvegarder les articles en JSON
def save_articles_to_json(articles, json_file):
    try:
        logging.info(f"Sauvegarde des articles dans le fichier JSON: {json_file}")

        if os.path.exists(json_file):
            # Charger les données existantes
            with open(json_file, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        # Ajouter les nouveaux articles
        existing_data.extend(articles)

        # Sauvegarder dans le fichier JSON
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)

        logging.info(f"{len(articles)} articles ont été sauvegardés dans {json_file}.")
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
            logging.warning("Aucun article trouvé dans la catégorie 'Artificial intelligence'.")
    except Exception as e:
        logging.error(f"Erreur lors de l'exécution : {e}")

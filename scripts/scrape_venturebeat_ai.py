import feedparser
from datetime import datetime
import json
import os
import requests
from bs4 import BeautifulSoup
import logging

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "venturebeat_articles.json")


# Charger ou initialiser les données JSON
def load_json_data():
    if os.path.exists(JSON_OUTPUT_FILE):
        with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as file:
            logging.info("Chargement des données JSON existantes.")
            return json.load(file)
    logging.info("Aucune donnée JSON existante, création d'un nouveau fichier.")
    return []


# Sauvegarder les articles dans le fichier JSON
def save_to_json(articles):
    existing_data = load_json_data()
    existing_links = {article["link"] for article in existing_data}

    # Ajouter uniquement les nouveaux articles
    new_articles = [article for article in articles if article["link"] not in existing_links]
    existing_data.extend(new_articles)

    # Écrire les données mises à jour dans le fichier
    with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)
    logging.info(f"{len(new_articles)} nouveaux articles ajoutés au fichier JSON.")


# Fonction pour valider et formater la date
def validate_and_format_date(date_str):
    if not date_str:
        logging.warning("Aucune date fournie pour l'article.")
        return None
    try:
        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return date_obj.date()
    except ValueError:
        logging.error(f"Erreur lors du parsing de la date : {date_str}")
        return None


# Fonction pour nettoyer le contenu HTML
def clean_html_content(content):
    soup = BeautifulSoup(content, "lxml")  # Parser le contenu HTML
    return soup.get_text()  # Extraire uniquement le texte brut


# Fonction pour récupérer le contenu complet d'un article
def fetch_full_content(url):
    """
    Récupère le contenu complet d'un article depuis l'URL donnée.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # VentureBeat : Contenu principal de l'article
        article_body = soup.find("div", class_="article-content")

        if not article_body:
            logging.warning(f"Impossible de trouver le contenu principal pour : {url}")
            return None

        # Extraire le texte
        full_content = article_body.get_text(separator=" ").strip()
        return full_content
    except Exception as e:
        logging.error(f"Erreur lors de la récupération du contenu pour {url} : {e}")
        return None


# Fonction pour traiter chaque article du flux RSS
def process_feed(feed_url):
    logging.info(f"Récupération du flux RSS depuis {feed_url}")
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        logging.warning("Aucun article trouvé dans le flux RSS.")
        return

    articles_to_save = []
    for entry in feed.entries:
        title = entry.title
        link = entry.link

        # Extraction de l'auteur via dc:creator ou une valeur par défaut
        author = entry.get("dc:creator") or entry.get("author", "Unknown")

        # Extraire le résumé ou description
        summary = entry.get("summary", "No summary available.")
        summary = clean_html_content(summary)

        # Validation et formatage de la date de publication
        publication_date = validate_and_format_date(entry.get("published"))

        # Récupérer le contenu complet de l'article
        full_content = fetch_full_content(link)

        article = {
            "title": title,
            "source": "VentureBeat",
            "publication_date": publication_date.isoformat() if publication_date else None,
            "summary": summary,
            "full_content": full_content,
            "language": "english",
            "link": link,
            "author": author
        }

        # Ajouter l'article à la liste pour le JSON
        articles_to_save.append(article)

    # Enregistrer les articles dans le fichier JSON
    save_to_json(articles_to_save)


# Fonction principale
def main():
    logging.info("Démarrage du traitement des articles.")
    
    # Flux RSS pour VentureBeat
    venturebeat_feed_url = "https://venturebeat.com/category/ai/feed/"
    process_feed(venturebeat_feed_url)

    logging.info("Traitement terminé.")


if __name__ == "__main__":
    main()

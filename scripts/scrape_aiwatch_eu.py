import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# URL du flux RSS
RSS_URL = "https://ai-watch.ec.europa.eu/node/2/rss_en"

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "aiwatch_articles.json")


def load_existing_articles():
    """
    Charge les articles existants depuis le fichier JSON.
    """
    if os.path.exists(JSON_OUTPUT_FILE):
        try:
            with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as json_file:
                return json.load(json_file)
        except (IOError, json.JSONDecodeError):
            print("Erreur lors du chargement des articles existants.")
    return []


def save_to_json(articles):
    """
    Sauvegarde les articles dans un fichier JSON.
    """
    try:
        with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
            json.dump(articles, json_file, indent=4, ensure_ascii=False)
        print(f"Articles sauvegardés dans {JSON_OUTPUT_FILE}.")
    except IOError as e:
        print(f"Erreur lors de l'écriture du fichier JSON : {e}")


def fetch_full_content(url):
    """
    Récupère le contenu complet d'un article à partir de son URL.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            print("Trop de requêtes ! Pause de 60 secondes.")
            time.sleep(60)
            return fetch_full_content(url)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_body = soup.find("article")

        if not article_body:
            print(f"Aucun contenu trouvé pour l'URL {url}.")
            return None

        paragraphs = [p.get_text(strip=True) for p in article_body.find_all("p")]
        return "\n".join(paragraphs) if paragraphs else None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'article {url} : {e}")
        return None


def parse_rss_feed():
    """
    Scrape les articles à partir du flux RSS.
    """
    articles = []
    try:
        response = requests.get(RSS_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        # Charger les articles existants
        existing_articles = load_existing_articles()
        existing_links = {article["link"] for article in existing_articles}

        for item in items:
            title = item.find("title").text.strip() if item.find("title") else "No title"
            link = item.find("link").text.strip() if item.find("link") else None

            # Éviter les doublons
            if link in existing_links:
                print(f"Article déjà existant, ignoré : {title}")
                continue

            summary = item.find("description").text.strip() if item.find("description") else "No summary available."
            if summary != "No summary available.":
                summary = BeautifulSoup(summary, "html.parser").get_text().strip()

            pub_date = item.find("pubDate").text.strip() if item.find("pubDate") else None
            if pub_date:
                try:
                    pub_date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
                except ValueError as e:
                    print(f"Erreur lors de la conversion de la date : {e}")
                    pub_date = None

            # Champs fixes
            source = "AI Watch European Commission"
            author = "AI Watch"
            language = "english"

            # Récupérer le contenu complet de l'article
            full_content = fetch_full_content(link)

            # Préparer les données de l'article
            article_data = {
                "title": title,
                "source": source,
                "publication_date": pub_date,
                "link": link,
                "author": author,
                "summary": summary,
                "full_content": full_content,
                "language": language,
            }

            # Ajouter l'article à la liste
            articles.append(article_data)
            existing_links.add(link)  # Ajouter le lien à l'ensemble pour éviter les doublons
            print(f"Article ajouté : {title}")
            time.sleep(2)  # Pause pour éviter trop de requêtes rapides

        # Fusionner les articles existants et les nouveaux
        all_articles = existing_articles + articles

        # Sauvegarder tous les articles dans un fichier JSON
        save_to_json(all_articles)

    except Exception as e:
        print(f"Erreur lors du scraping du flux RSS : {e}")


if __name__ == "__main__":
    parse_rss_feed()

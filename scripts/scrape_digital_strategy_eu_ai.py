import os
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# URL de base pour Digital Strategy
BASE_URL = "https://digital-strategy.ec.europa.eu"
PAGE_URL = "/en/related-content?topic=119"

# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "digital_strategy_articles.json")


def load_existing_articles():
    """Charge les articles existants depuis le fichier JSON."""
    if os.path.exists(JSON_OUTPUT_FILE):
        with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_to_json(articles):
    """Sauvegarde les articles dans le fichier JSON."""
    with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(articles, file, indent=4, ensure_ascii=False)
    print(f"{len(articles)} articles sauvegardés dans le fichier JSON.")


def extract_date(article):
    """Extrait et formate la date de publication de l'article."""
    time_tag = article.find("time")
    if time_tag:
        date_str = time_tag.get("datetime", "").strip()
        if date_str:
            for fmt in ("%d %B %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            print(f"Format de date non pris en charge : {date_str}")
    return None


def fetch_digital_strategy_content(url):
    """Récupère et parse le contenu complet d'un article Digital Strategy."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        main_content = soup.find("div", class_="cnt-main-body")

        if main_content:
            paragraphs = [p.get_text(strip=True) for p in main_content.find_all("p")]
            return "\n".join(paragraphs)
        else:
            print(f"Aucun contenu trouvé pour l'URL {url}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'article {url} : {e}")
        return None


def scrape_page(url):
    """Scrape les articles à partir de la page spécifiée."""
    response = requests.get(urljoin(BASE_URL, url))
    if response.status_code != 200:
        print(f"Erreur HTTP : {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="ecl-u-d-flex")

    scraped_articles = []
    for article in articles:
        title_tag = article.find("a", class_="ecl-link")
        title = title_tag.text.strip() if title_tag else "No title"
        link = urljoin(BASE_URL, title_tag["href"]) if title_tag else None

        publication_date = extract_date(article)

        summary_tag = article.find("div", class_="cnt-teaser")
        summary = summary_tag.text.strip() if summary_tag else "No summary available."

        # Récupérer le contenu complet
        full_content = fetch_digital_strategy_content(link) if link else None

        # Champs fixes
        source = "Digital Strategy"
        author = "European Commission"
        language = "english"

        # Structure des données
        article_data = {
            "title": title,
            "source": source,
            "publication_date": publication_date,
            "link": link,
            "author": author,
            "full_content": full_content,
            "summary": summary,
            "language": language,
        }

        scraped_articles.append(article_data)
        time.sleep(2)  # Pause pour éviter de surcharger le serveur

    return scraped_articles


if __name__ == "__main__":
    # Charger les articles existants
    existing_articles = load_existing_articles()
    existing_links = {article["link"] for article in existing_articles}

    # Scraper les nouveaux articles
    new_articles = scrape_page(PAGE_URL)

    # Filtrer les articles déjà présents
    unique_articles = [article for article in new_articles if article["link"] not in existing_links]

    # Ajouter les nouveaux articles uniques à la liste existante avec `extend`
    existing_articles.extend(unique_articles)

    # Sauvegarder les données dans le fichier JSON
    save_to_json(existing_articles)

    print(f"Nombre d'articles ajoutés : {len(unique_articles)}")

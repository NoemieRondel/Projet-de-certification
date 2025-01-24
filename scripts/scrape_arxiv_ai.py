import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import os
import logging
import json

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Fonction pour parser et récupérer les articles
def fetch_arxiv_articles():
    logging.info("Récupération des articles depuis ArXiv...")
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "all:artificial intelligence",
        "start": 0,
        "max_results": 50,
    }
    articles = []
    while True:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        xml_data = response.text

        root = ET.fromstring(xml_data)
        new_articles = 0
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title")
            if title is None:
                continue
            title = title.text.strip()
            abstract = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
            published = entry.find("{http://www.w3.org/2005/Atom}published").text.strip()
            authors = ", ".join(
                [
                    author.find("{http://www.w3.org/2005/Atom}name").text.strip()
                    for author in entry.findall("{http://www.w3.org/2005/Atom}author")
                ]
            )
            article_url = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()
            arxiv_id = article_url.split("/")[-1]

            articles.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "publication_date": published,  # Utilisation d'une chaîne de caractères
                    "authors": authors,
                    "article_url": article_url,
                    "external_id": arxiv_id,
                    "source": "ArXiv",
                }
            )
            new_articles += 1

        logging.info(f"{new_articles} nouveaux articles récupérés.")
        if new_articles == 0:
            break
        params["start"] += 50
    return articles


# Fonction pour sauvegarder les articles dans un fichier JSON
def save_articles_to_json(articles):
    json_file_path = "arxiv_articles.json"
    if os.path.exists(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = []

    # Ajouter les nouveaux articles
    existing_data.extend(articles)

    # Sauvegarder les articles dans le fichier JSON
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

    logging.info(f"{len(articles)} articles ont été sauvegardés dans '{json_file_path}'.")


# Script principal
if __name__ == "__main__":
    articles = fetch_arxiv_articles()
    if articles:
        save_articles_to_json(articles)
    else:
        logging.info("Aucun article collecté.")

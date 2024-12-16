import requests
import xml.etree.ElementTree as ET
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

# Chargement des variables d'environnement
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Fonction pour parser et récupérer les articles
def fetch_arxiv_articles():
    logging.info("Récupération des articles depuis ArXiv...")
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "all:artificial intelligence",
        "start": 0,
        "max_results": 50
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
            authors = ", ".join([author.find("{http://www.w3.org/2005/Atom}name").text.strip() for author in entry.findall("{http://www.w3.org/2005/Atom}author")])
            article_url = entry.find("{http://www.w3.org/2005/Atom}id").text.strip()
            arxiv_id = article_url.split("/")[-1]
            
            articles.append({
                "title": title,
                "abstract": abstract,
                "publication_date": datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").date(),
                "authors": authors,
                "article_url": article_url,
                "external_id": arxiv_id,
                "source": "ArXiv"
            })
            new_articles += 1

        logging.info(f"{new_articles} nouveaux articles récupérés.")
        if new_articles == 0:
            break
        params["start"] += 50
    return articles


# Fonction pour sauvegarder dans la base de données
def save_articles_to_db(articles):
    try:
        logging.info("Connexion à la base de données...")
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO scientific_articles (title, abstract, publication_date, authors, article_url, external_id, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            title = VALUES(title), abstract = VALUES(abstract), publication_date = VALUES(publication_date)
        """
        for article in articles:
            cursor.execute(insert_query, (
                article["title"],
                article["abstract"],
                article["publication_date"],
                article["authors"],
                article["article_url"],
                article["external_id"],
                article["source"]
            ))
        connection.commit()
        logging.info(f"{cursor.rowcount} articles ajoutés ou mis à jour.")
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        logging.error(f"Erreur MySQL : {err}")


# Script principal
if __name__ == "__main__":
    articles = fetch_arxiv_articles()
    if articles:
        save_articles_to_db(articles)
    else:
        logging.info("Aucun article collecté.")

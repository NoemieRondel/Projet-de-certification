import os
import json
import mysql.connector
from datetime import datetime
import feedparser
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# URL du flux RSS
RSS_URL = "https://www.technologyreview.com/feed/"


# Dossier pour les fichiers JSON
JSON_OUTPUT_DIR = "articles_outputs"
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
JSON_OUTPUT_FILE = os.path.join(JSON_OUTPUT_DIR, "mit_articles.json")


# Fonction pour récupérer les articles depuis un flux RSS
def fetch_rss_articles(rss_url):
    feed = feedparser.parse(rss_url)
    articles = []

    print(f"Nombre d'articles trouvés dans le flux : {len(feed.entries)}")
    for entry in feed.entries:
        print("\n--- Article brut ---")
        print(entry)  # Affiche toutes les données de l'article pour inspection

        # Vérifier si la catégorie correspond à "Artificial Intelligence"
        if 'category' in entry:
            print(f"Catégorie trouvée : {entry.category}")
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
            print("Aucune catégorie trouvée pour cet article.")

    print(f"Nombre d'articles filtrés : {len(articles)}")
    return articles


# Fonction pour sauvegarder les articles en JSON
def save_articles_to_json(articles, json_file):
    try:
        if os.path.exists(json_file):
            # Charger les données existantes
            with open(json_file, "r") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        # Ajouter les nouveaux articles
        existing_data.extend(articles)

        # Sauvegarder dans le fichier JSON
        with open(json_file, "w") as file:
            json.dump(existing_data, file, indent=4)

        print(f"{len(articles)} articles ont été sauvegardés dans {json_file}.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des articles en JSON : {e}")


# Fonction pour insérer ou mettre à jour les articles dans la base de données
def insert_articles_and_content_to_db(articles):
    try:
        # Connexion à la base de données
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Requêtes SQL
        insert_article = """
            INSERT INTO articles (title, author, publication_date, language, link, source, full_content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                author = VALUES(author),
                publication_date = VALUES(publication_date),
                source = VALUES(source),
                full_content = VALUES(full_content)
        """

        # Parcours des articles
        for article in articles:
            # Insérer ou mettre à jour l'article
            cursor.execute(insert_article, (
                article["title"],
                article["author"],
                article["publication_date"],
                article["language"],
                article["link"],
                article["source"],
                article["full_content"]
            ))

        # Commit et fermeture de la connexion
        conn.commit()
        cursor.close()
        conn.close()

        print("Les articles ont été insérés ou mis à jour dans la base de données.")
    except mysql.connector.Error as e:
        print(f"Erreur MySQL : {e}")


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        articles = fetch_rss_articles(RSS_URL)
        if articles:
            save_articles_to_json(articles, JSON_OUTPUT_FILE)
            insert_articles_and_content_to_db(articles)
            print("Les articles et leur contenu ont été traités avec succès.")
        else:
            print("Aucun article trouvé dans la catégorie 'Artificial intelligence'.")
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")

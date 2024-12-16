import os
import mysql.connector
from datetime import datetime
import feedparser
from dotenv import load_dotenv
from bs4 import BeautifulSoup

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
RSS_URL = "https://techcommunity.microsoft.com/t5/s/gxcuf89792/rss/Category?category.id=AI"


# Fonction pour récupérer les articles depuis un flux RSS
def fetch_rss_articles(rss_url):
    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries:
        # Nettoyer le contenu HTML dans la description
        raw_content = entry.description if 'description' in entry else None
        clean_content = clean_html(raw_content) if raw_content else None

        article = {
            "title": entry.title,
            "author": entry.author if 'author' in entry else None,
            "publication_date": datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None,
            "language": "english",
            "link": entry.link,
            "source": "Tech Community Microsoft",
            "content": clean_content
        }
        articles.append(article)

    return articles


# Fonction pour nettoyer le contenu HTML
def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(strip=True)


# Fonction pour insérer ou mettre à jour les articles dans la base de données
def insert_articles_and_content_to_db(articles):
    # Connexion à la base de données
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Requêtes SQL
    insert_article = """
        INSERT INTO articles (title, author, publication_date, language, link, source)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            author = VALUES(author),
            publication_date = VALUES(publication_date),
            source = VALUES(source)
    """
    insert_content = """
        INSERT INTO article_content (article_id, content)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            content = VALUES(content)
    """
    get_article_id = "SELECT id FROM articles WHERE link = %s"

    # Parcours des articles
    for article in articles:
        # Insérer ou mettre à jour l'article
        cursor.execute(insert_article, (
            article["title"],
            article["author"],
            article["publication_date"],
            article["language"],
            article["link"],
            article["source"]
        ))

        # Récupérer l'ID de l'article (soit inséré soit existant)
        cursor.execute(get_article_id, (article["link"],))
        result = cursor.fetchone()
        article_id = result[0] if result else None

        if article_id:
            # Insérer ou mettre à jour le contenu associé
            cursor.execute(insert_content, (article_id, article["content"]))

    # Commit et fermeture de la connexion
    conn.commit()
    cursor.close()
    conn.close()


# Exemple d'utilisation
if __name__ == "__main__":
    try:
        articles = fetch_rss_articles(RSS_URL)
        if articles:
            insert_articles_and_content_to_db(articles)
            print("Les articles et leur contenu ont été insérés ou mis à jour avec succès.")
        else:
            print("Aucun article trouvé dans le flux RSS.")
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")

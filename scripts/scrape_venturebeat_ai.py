import mysql.connector
import feedparser
from datetime import datetime
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# Connexion à la base de données
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("Connexion réussie à la base de données.")
        return connection
    except mysql.connector.Error as err:
        print(f"Erreur de connexion : {err}")
        return None


# Fonction pour valider et formater la date
def validate_and_format_date(date_str):
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return date_obj.date()
    except ValueError:
        print(f"Erreur lors du parsing de la date : {date_str}")
        return None


# Fonction pour nettoyer le contenu HTML
def clean_html_content(content):
    soup = BeautifulSoup(content, "lxml")  # Parser le contenu HTML
    return soup.get_text()  # Extraire uniquement le texte brut


# Fonction pour traiter chaque article du flux RSS
def process_feed(feed_url, connection):
    print(f"Récupération du flux RSS depuis {feed_url}")
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print("Aucun article trouvé dans le flux RSS.")
        return

    cursor = connection.cursor()
    for entry in feed.entries:
        title = entry.title
        link = entry.link

        # Extraction de l'auteur via dc:creator ou une valeur par défaut
        author = entry.get("dc:creator") or entry.get("author", "Unknown")

        # Extraire le contenu de description ou content
        content = entry.get("content", [{}])[0].get("value", entry.get("description", "No content"))
        content = clean_html_content(content)

        # Validation et formatage de la date de publication
        publication_date = validate_and_format_date(entry.get("published"))

        # Vérifier si l'article existe déjà dans la base de données
        cursor.execute("SELECT COUNT(*) FROM articles WHERE link = %s", (link,))
        article_exists = cursor.fetchone()[0] > 0

        if article_exists:
            print(f"L'article '{title}' existe déjà. Mise à jour en cours...")
            update_query = """
                UPDATE articles
                SET title = %s,
                    source = %s,
                    publication_date = %s,
                    content = %s,
                    language = %s,
                    author = %s
                WHERE link = %s
            """
            cursor.execute(update_query, (
                title,
                "VentureBeat",
                publication_date,
                content,
                "english",
                author,
                link
            ))
        else:
            print(f"Insertion de l'article '{title}' dans la base de données...")
            insert_query = """
                INSERT INTO articles (title, source, publication_date, content, language, link, author)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                title,
                "VentureBeat",
                publication_date,
                content,
                "english",
                link,
                author
            ))

    connection.commit()
    print(f"Traitement du flux RSS '{feed_url}' terminé.")
    cursor.close()


# Fonction principale
def main():
    connection = connect_to_database()
    if connection is None:
        print("Impossible de se connecter à la base de données. Fin du programme.")
        return

    # Flux RSS pour VentureBeat
    venturebeat_feed_url = "https://venturebeat.com/category/ai/feed/"
    process_feed(venturebeat_feed_url, connection)

    connection.close()
    print("Connexion à la base de données fermée.")


if __name__ == "__main__":
    main()

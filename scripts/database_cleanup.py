import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from urllib.parse import urlparse

# Chargement des variables d'environnement
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("db_cleaning.log"),
        logging.StreamHandler()  # Affiche aussi dans le terminal
    ]
)


def connect_to_database():
    """Établit une connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def check_empty_fields(cursor, table, fields):
    """Vérifie les champs vides dans une table donnée et retourne les anomalies."""
    anomalies = {}
    for field in fields:
        if "date" in field.lower():  # Vérification spécifique pour les champs de type date
            query = f"SELECT id FROM {table} WHERE {field} IS NULL;"
        else:
            query = f"SELECT id FROM {table} WHERE {field} IS NULL OR {field} = '';"
        cursor.execute(query)
        anomalies[field] = cursor.fetchall()
    return anomalies


def delete_invalid_links(cursor):
    """Supprime les articles avec des liens invalides."""
    cursor.execute("SELECT id, link FROM articles WHERE link IS NOT NULL")
    links = cursor.fetchall()

    # Modification ici pour accéder aux données par clé
    invalid_links = [row['id'] for row in links if not urlparse(row['link']).scheme or not urlparse(row['link']).netloc]

    if invalid_links:
        cursor.execute(f"DELETE FROM articles WHERE id IN ({', '.join(map(str, invalid_links))})")
        logging.info(f"{len(invalid_links)} article(s) supprimé(s) pour liens invalides.")



def delete_empty_articles(cursor):
    """Supprime les articles avec des champs critiques manquants."""
    cursor.execute("""
        DELETE FROM articles
        WHERE title IS NULL OR publication_date IS NULL OR summary IS NULL OR full_content IS NULL OR author IS NULL
    """)
    rows_deleted = cursor.rowcount
    logging.info(f"{rows_deleted} article(s) supprimé(s) pour champs critiques vides.")


def delete_duplicates(cursor):
    """Supprime les doublons en gardant l'article au plus petit ID."""
    cursor.execute("""
        DELETE a1
        FROM articles a1
        INNER JOIN articles a2
        ON a1.id > a2.id AND a1.link = a2.link
    """)
    rows_deleted = cursor.rowcount
    logging.info(f"{rows_deleted} doublon(s) supprimé(s).")


def archive_irrelevant_articles(cursor):
    """Déplace les articles sans mots-clés vers la table 'irrelevant_articles'."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS irrelevant_articles AS 
        SELECT * FROM articles WHERE keywords IS NULL;
    """)
    cursor.execute("DELETE FROM articles WHERE keywords IS NULL;")
    rows_deleted = cursor.rowcount
    logging.info(f"{rows_deleted} article(s) déplacé(s) vers 'irrelevant_articles' et supprimé(s) de 'articles'.")


def clean_database():
    """Point d'entrée principal pour la vérification et le nettoyage de la base de données."""
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        logging.info("Début du nettoyage de la base de données.")

        # Vérification des champs critiques pour les articles
        fields_articles = ["title", "publication_date", "summary", "full_content", "author"]
        anomalies = check_empty_fields(cursor, "articles", fields_articles)
        for field, rows in anomalies.items():
            logging.info(f"{len(rows)} article(s) avec le champ '{field}' vide.")

        # Suppressions et archivage
        delete_invalid_links(cursor)
        delete_empty_articles(cursor)
        delete_duplicates(cursor)
        archive_irrelevant_articles(cursor)

        # Appliquer les changements
        connection.commit()
        logging.info("Nettoyage terminé et changements appliqués.")

    except Error as e:
        logging.error(f"Erreur lors de l'opération : {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            logging.info("Connexion à la base de données fermée.")


if __name__ == "__main__":
    clean_database()

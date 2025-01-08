import os
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement pour la connexion à la base de données
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


def connect_to_database():
    """Se connecter à la base de données MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def check_empty_fields(cursor, table, field):
    """Vérifie les champs vides dans une table donnée."""
    query = f"SELECT id FROM {table} WHERE {field} IS NULL OR {field} = '';"
    cursor.execute(query)
    return cursor.fetchall()


def check_broken_relations(cursor):
    """Vérifie les relations cassées entre articles et article_content."""
    query = """
    SELECT ac.article_id
    FROM article_content ac
    LEFT JOIN articles a ON ac.article_id = a.id
    WHERE a.id IS NULL;
    """
    cursor.execute(query)
    return cursor.fetchall()


def main():
    """Point d'entrée principal pour exécuter les vérifications."""
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        print("\n--- Vérification des champs vides ---")
        empty_titles = check_empty_fields(cursor, "articles", "title")
        empty_links = check_empty_fields(cursor, "articles", "link")
        print(f"Articles avec titres vides : {len(empty_titles)}")
        print(f"Articles avec liens vides : {len(empty_links)}")

        print("\n--- Vérification des relations cassées ---")
        broken_relations = check_broken_relations(cursor)
        print(f"Relations cassées (article_content -> articles) : {len(broken_relations)}")
        if broken_relations:
            print("ID des relations cassées : ", [rel['article_id'] for rel in broken_relations])

    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConnexion fermée.")


if __name__ == "__main__":
    main()

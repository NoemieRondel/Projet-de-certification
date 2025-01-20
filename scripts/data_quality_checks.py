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
    if "date" in field.lower():  # Si le champ est de type 'date', on ne vérifie que pour NULL
        query = f"SELECT id FROM {table} WHERE {field} IS NULL;"
    else:  # Sinon, on vérifie si le champ est NULL ou vide
        query = f"SELECT id FROM {table} WHERE {field} IS NULL OR {field} = '';"

    cursor.execute(query)
    return cursor.fetchall()


def main():
    """Point d'entrée principal pour exécuter les vérifications."""
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        # Vérification des champs vides dans la table articles
        print("\n--- Vérification des champs vides (articles) ---")
        empty_titles = check_empty_fields(cursor, "articles", "title")
        empty_publication_date = check_empty_fields(cursor, "articles", "publication_date")
        empty_summary = check_empty_fields(cursor, "articles", "summary")
        empty_full_content = check_empty_fields(cursor, "articles", "full_content")
        empty_author = check_empty_fields(cursor, "articles", "author")
        print(f"Articles avec titres vides : {len(empty_titles)}")
        print(f"Articles avec dates de publication vides : {len(empty_publication_date)}")
        print(f"Articles avec résumés vides : {len(empty_summary)}")
        print(f"Articles avec contenus complets vides : {len(empty_full_content)}")
        print(f"Articles avec auteurs vides : {len(empty_author)}")

        # Vérification des champs vides dans la table scientific_articles
        print("\n--- Vérification des champs vides (scientific_articles) ---")
        empty_titles_scientific = check_empty_fields(cursor, "scientific_articles", "title")
        empty_abstracts = check_empty_fields(cursor, "scientific_articles", "abstract")
        empty_keywords = check_empty_fields(cursor, "scientific_articles", "keywords")
        empty_publication_date_scientific = check_empty_fields(cursor, "scientific_articles", "publication_date")
        empty_author_scientific = check_empty_fields(cursor, "scientific_articles", "authors")
        print(f"Articles scientifiques avec titles vides : {len(empty_titles_scientific)}")
        print(f"Articles scientifiques avec abstracts vides : {len(empty_abstracts)}")
        print(f"Articles scientifiques avec mots-clés vides : {len(empty_keywords)}")
        print(f"Articles scientifiques avec dates de publication vides : {len(empty_publication_date_scientific)}")
        print(f"Articles scientifiques avec auteurs vides : {len(empty_author_scientific)}")

    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConnexion fermée.")


if __name__ == "__main__":
    main()

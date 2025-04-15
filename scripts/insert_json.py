import mysql.connector
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

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


# Normaliser les formats de date
def normalize_date_format(date_string):
    if not date_string:
        return None
    try:
        parsed_date = datetime.fromisoformat(date_string)
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        try:
            parsed_date = datetime.strptime(date_string, "%d/%m/%Y")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Format de date non reconnu : {date_string}")
            return None


# Charger le fichier JSON
def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        print(f"{len(data) if isinstance(data, list) else 1} enregistrements chargés depuis {file_path}.")
        # Normalisation des dates pour les formats articles / scientifiques / vidéos
        if isinstance(data, list):
            for item in data:
                if "publication_date" in item:
                    item["publication_date"] = normalize_date_format(item["publication_date"])
        elif isinstance(data, dict) and "publication_date" in data:
            data["publication_date"] = normalize_date_format(data["publication_date"])
        return data
    except FileNotFoundError:
        print(f"Le fichier {file_path} n'existe pas.")
        return []
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON dans {file_path} : {e}")
        return []


# Insérer ou mettre à jour les données
def insert_or_update_data(table_name, data, connection):
    cursor = connection.cursor()
    inserted = 0
    updated = 0

    if table_name == "articles":
        query_check = "SELECT COUNT(*) FROM articles WHERE link = %s"
        query_insert = """
            INSERT INTO articles (title, source, publication_date, summary,
            full_content, language, link, author, keywords)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        query_update = """
            UPDATE articles SET title = %s, source = %s, publication_date = %s,
            summary = %s, full_content = %s, language = %s, author = %s, keywords = %s
            WHERE link = %s
        """
    elif table_name == "scientific_articles":
        query_check = "SELECT COUNT(*) FROM scientific_articles WHERE external_id = %s"
        query_insert = """
            INSERT INTO scientific_articles (title, authors, publication_date,
            abstract, article_url, external_id, keywords, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        query_update = """
            UPDATE scientific_articles SET title = %s, authors = %s, publication_date = %s,
            abstract = %s, keywords = %s, source = %s, article_url = %s
            WHERE external_id = %s
        """
    elif table_name == "videos":
        query_check = "SELECT COUNT(*) FROM videos WHERE video_url = %s"
        query_insert = """
            INSERT INTO videos (title, description, publication_date, source,
            video_url, channel_name, channel_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        query_update = """
            UPDATE videos SET title = %s, description = %s, publication_date = %s,
            source = %s, channel_name = %s, channel_id = %s
            WHERE video_url = %s
        """
    else:
        print(f"Table inconnue : {table_name}")
        return

    for item in data:
        unique_key = None
        if table_name == "articles":
            unique_key = item.get("link")
        elif table_name == "scientific_articles":
            unique_key = item.get("external_id")
        elif table_name == "videos":
            unique_key = item.get("video_url")

        if not unique_key:
            print(f"Enregistrement ignoré (clé unique manquante) : {item}")
            continue

        cursor.execute(query_check, (unique_key,))
        exists = cursor.fetchone()[0] > 0

        if exists:
            if table_name == "articles":
                cursor.execute(query_update, (
                    item.get("title"), item.get("source"), item.get("publication_date"),
                    item.get("summary"), item.get("full_content"), item.get("language"),
                    item.get("author"), item.get("keywords"), unique_key
                ))
            elif table_name == "scientific_articles":
                cursor.execute(query_update, (
                    item.get("title"), item.get("authors"), item.get("publication_date"),
                    item.get("abstract"), item.get("keywords"), item.get("source"),
                    item.get("article_url"), unique_key
                ))
            elif table_name == "videos":
                cursor.execute(query_update, (
                    item.get("title"), item.get("description"), item.get("publication_date"),
                    item.get("source"), item.get("channel_name"), item.get("channel_id"),
                    unique_key
                ))
            updated += 1
        else:
            if table_name == "articles":
                cursor.execute(query_insert, (
                    item.get("title"), item.get("source"), item.get("publication_date"),
                    item.get("summary"), item.get("full_content"), item.get("language"),
                    unique_key, item.get("author"), item.get("keywords")
                ))
            elif table_name == "scientific_articles":
                cursor.execute(query_insert, (
                    item.get("title"), item.get("authors"), item.get("publication_date"),
                    item.get("abstract"), item.get("article_url"), unique_key,
                    item.get("keywords"), item.get("source")
                ))
            elif table_name == "videos":
                cursor.execute(query_insert, (
                    item.get("title"), item.get("description"), item.get("publication_date"),
                    item.get("source"), unique_key, item.get("channel_name"), item.get("channel_id")
                ))
            inserted += 1

    connection.commit()
    print(f"Table {table_name} : {inserted} enregistrements insérés, {updated} enregistrements mis à jour.")
    cursor.close()


# Insertion dans monitoring_logs
def insert_monitoring_logs(data, connection):
    cursor = connection.cursor()
    inserted = 0

    # Vérification si les données sont encapsulées sous la clé 'entries'
    if isinstance(data, dict) and 'entries' in data:
        data = data['entries']

    for entry in data:
        timestamp = entry.get("timestamp")
        script = entry.get("script")

        if not timestamp or not script:
            print(f"Entrée ignorée (timestamp ou script manquant) : {entry}")
            continue

        cursor.execute("""
            SELECT COUNT(*) FROM monitoring_logs WHERE timestamp = %s AND script = %s
        """, (timestamp, script))
        if cursor.fetchone()[0] > 0:
            continue

        cursor.execute("""
            INSERT INTO monitoring_logs (
                timestamp, script, duration_seconds,
                articles_count, empty_full_content_count, average_keywords_per_article,
                summaries_generated, average_summary_word_count,
                scientific_articles_count, empty_abstracts_count, average_keywords_per_scientific_article
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            script,
            entry.get("duration_seconds"),
            entry.get("articles_count"),
            entry.get("empty_full_content_count"),
            entry.get("average_keywords_per_article"),
            entry.get("summaries_generated"),
            entry.get("average_summary_word_count"),
            entry.get("scientific_articles_count"),
            entry.get("empty_abstracts_count"),
            entry.get("average_keywords_per_scientific_article")
        ))

        inserted += 1

    connection.commit()
    print(f"Table monitoring_logs : {inserted} entrées insérées.")
    cursor.close()


# Fonction principale
def main():
    connection = connect_to_database()
    if not connection:
        print("Impossible de se connecter à la base de données. Fin du programme.")
        return

    json_files_and_tables = {
        "articles.json": "articles",
        "arxiv_articles.json": "scientific_articles",
        "videos.json": "videos",
        "monitoring.json": "monitoring_logs"
    }

    for json_file, table_name in json_files_and_tables.items():
        print(f"Traitement de {json_file}...")
        data = load_json_file(json_file)
        if table_name == "monitoring_logs":
            insert_monitoring_logs(data, connection)
        else:
            insert_or_update_data(table_name, data, connection)

    print("Fin du traitement des fichiers JSON.")


if __name__ == "__main__":
    main()

import mysql.connector
from mysql.connector import Error
from urllib.parse import urlparse
from dotenv import load_dotenv
import os

# Charger les variables d'environnement depuis .env
load_dotenv()


def delete_anomalies():
    try:
        # Connexion à la base de données
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Sélection explicite de la base de données (utiliser DATANAME ici)
            cursor.execute(f"USE {os.getenv('DB_NAME')}")

            # Supprimer les articles avec des champs critiques manquants
            print("=== Suppression des articles avec des champs critiques manquants ===")
            cursor.execute("""
                DELETE FROM articles
                WHERE title IS NULL OR publication_date IS NULL OR content IS NULL OR link IS NULL
            """)
            rows_deleted = cursor.rowcount
            print(f"{rows_deleted} article(s) supprimé(s) pour champs manquants.")

            # Supprimer les doublons (en gardant l'article au plus petit ID)
            print("\n=== Suppression des doublons ===")
            cursor.execute("""
                DELETE a1
                FROM articles a1
                INNER JOIN articles a2
                ON a1.id > a2.id AND a1.link = a2.link
            """)
            rows_deleted = cursor.rowcount
            print(f"{rows_deleted} doublon(s) supprimé(s).")

            # Supprimer les articles avec des liens invalides
            print("\n=== Suppression des articles avec des liens invalides ===")
            cursor.execute("""
                SELECT id, link
                FROM articles
                WHERE link IS NOT NULL
            """)
            links = cursor.fetchall()

            invalid_links = []
            for row in links:
                parsed = urlparse(row[1])  # row[1] = link
                if not parsed.scheme or not parsed.netloc:
                    invalid_links.append(row[0])  # row[0] = id

            if invalid_links:
                # Supprimer les articles avec liens invalides
                cursor.execute(f"""
                    DELETE FROM articles
                    WHERE id IN ({', '.join(map(str, invalid_links))})
                """)
                print(f"{len(invalid_links)} article(s) supprimé(s) pour liens invalides.")
            else:
                print("Aucun lien invalide détecté.")

            # Appliquer les changements
            connection.commit()
            print("\nToutes les anomalies ont été traitées et les suppressions appliquées.")

    except Error as e:
        print(f"Erreur : {e}")

    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("\nConnexion à la base de données fermée.")
        except UnboundLocalError:
            print("La connexion n'a pas pu être établie. Vérifiez vos paramètres.")


if __name__ == "__main__":
    delete_anomalies()

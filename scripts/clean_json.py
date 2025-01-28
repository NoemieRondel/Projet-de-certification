import os
import re
import mysql.connector
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration simple du logging affiché dans le terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def connect_to_database():
    """Connexion à la base de données via les variables d'environnement."""
    logging.info("Tentative de connexion à la base de données...")
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        logging.info("Connexion réussie à la base de données.")
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Erreur de connexion : {err}")
        raise


def clean_text(text):
    """Nettoie un texte en supprimant les éléments inutiles."""
    if not text:
        return None

    # Suppression des balises HTML
    text = BeautifulSoup(text, "html.parser").get_text()

    # Liste de termes superflus à filtrer
    noise_terms = [
        "click here", "read more", "terms and conditions", "privacy policy",
        "sign up", "subscribe", "learn more", "advertisement", "copyright",
        "all rights reserved", "powered by", "follow us", "get started"
    ]

    # Suppression des termes superflus
    for term in noise_terms:
        text = re.sub(rf"\b{re.escape(term)}\b", "", text, flags=re.IGNORECASE)

    # Suppression des caractères spéciaux et des espaces multiples
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)  # Garder uniquement lettres, chiffres, espaces
    text = re.sub(r"\s+", " ", text)  # Réduction des espaces multiples à un seul

    return text


def clean_database_texts(connection):
    """Nettoie les champs textuels dans la base de données."""
    tables_fields = {
        "articles": ["summary", "full_content"],
        "scientific_articles": ["abstract"],
        "videos": ["description"]
    }

    modified_count = 0  # Compteur des modifications

    try:
        cursor = connection.cursor()

        for table, fields in tables_fields.items():
            for field in fields:
                logging.info(f"Nettoyage du champ '{field}' de la table '{table}'...")

                # Sélection des ID et des champs non vides
                cursor.execute(f"SELECT id, {field} FROM {table} WHERE {field} IS NOT NULL AND {field} != '';")
                rows = cursor.fetchall()

                for row_id, text in rows:
                    cleaned_text = clean_text(text)
                    if cleaned_text != text:
                        # Mise à jour uniquement si le texte est modifié
                        cursor.execute(f"UPDATE {table} SET {field} = %s WHERE id = %s;", (cleaned_text, row_id))
                        modified_count += 1
                        logging.info(f"Texte nettoyé pour l'ID {row_id} dans la table '{table}', champ '{field}'.")

        connection.commit()
        logging.info(f"Nettoyage des textes terminé avec succès. Total des éléments modifiés : {modified_count}")

    except Exception as e:
        logging.error(f"Erreur lors du nettoyage : {e}")
    finally:
        cursor.close()


if __name__ == "__main__":
    try:
        connection = connect_to_database()
        clean_database_texts(connection)
    finally:
        connection.close()
        logging.info("Connexion à la base de données fermée.")

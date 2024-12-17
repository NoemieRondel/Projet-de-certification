import os
import spacy
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Initialiser spaCy (modèle anglais)
nlp = spacy.load("en_core_web_sm")  # Modèle de base pour détecter les entités


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def extract_technologies(text):
    """Extrait les entités ou les technologies) à partir du texte."""
    doc = nlp(text)
    technologies_found = set()

    # Parcourir les entités détectées par spaCy
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PRODUCT", "GPE"}:  # Types d'entités détectés
            technologies_found.add(ent.text)

    return ";".join(technologies_found)


def process_table(table_name, text_field, focus_field):
    """Parcourt une table pour remplir le champ focus_tech si vide."""
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    print(f"Processing table: {table_name}...")

    # Sélectionner les lignes où focus_field est NULL ou vide
    cursor.execute(f"SELECT id, {text_field} FROM {table_name} WHERE {focus_field} IS NULL OR {focus_field} = ''")
    rows = cursor.fetchall()

    for row in rows:
        text = row[text_field]
        if text:
            technologies = extract_technologies(text)
            if technologies:  # MAJ uniquement si des technos sont trouvées
                cursor.execute(
                    f"UPDATE {table_name} SET {focus_field} = %s WHERE id = %s",
                    (technologies, row['id'])
                )
                print(f"Updated row ID {row['id']} with technologies: {technologies}")

    db.commit()
    cursor.close()
    db.close()


if __name__ == "__main__":
    # Traiter chaque table
    process_table("articles", "content", "focus_tech")
    process_table("videos", "description", "focus_tech")

    print("Processing completed!")

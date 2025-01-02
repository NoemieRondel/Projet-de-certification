import os
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la connexion à la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Connexion à la base de données
connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = connection.cursor()

# Créer la table 'irrelevant_articles' pour stocker les articles sans mots-clés
cursor.execute("""
CREATE TABLE IF NOT EXISTS irrelevant_articles AS
SELECT * FROM articles WHERE keywords IS NULL;
""")

# Supprimer les articles sans mots-clés de la table 'articles'
cursor.execute("""
DELETE FROM articles WHERE keywords IS NULL;
""")

# Valider les changements
connection.commit()

# Fermer la connexion
cursor.close()
connection.close()

print("Les articles sans mots-clés ont été déplacés vers 'irrelevant_articles' et supprimés de 'articles'.")

import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

# Charger les variables d'environnement
load_dotenv(os.path.join(os.path.dirname(__file__), "../scripts/.env"))

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Configuration du pool de connexions
db_config = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "port": 3306,
    "pool_name": "my_pool",
    "pool_size": 10
}

# Ne pas initialiser le pool immédiatement
connection_pool = None


def get_connection():
    """Récupère une connexion depuis le pool, en l'initialisant si nécessaire."""
    global connection_pool
    try:
        if connection_pool is None:
            connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
        connection = connection_pool.get_connection()
        if connection.is_connected():
            print("Connexion réussie via le pool de connexions")
        return connection
    except mysql.connector.Error as e:
        print(f"Erreur de connexion au pool : {e}")
        return None

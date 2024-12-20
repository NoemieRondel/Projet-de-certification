import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def connect_db():
    """Connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


def fetch_digital_strategy_content(url):
    """Récupérer et parser le contenu d'un article Digital Strategy."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        # Gestion du cas où trop de requêtes sont envoyées
        if response.status_code == 429:
            print("Trop de requêtes ! Pause de 60 secondes.")
            time.sleep(60)
            return fetch_digital_strategy_content(url)

        response.raise_for_status()  # Vérifier si la requête s'est bien passée

        # Parser le contenu de la page
        soup = BeautifulSoup(response.text, 'html.parser')
        main_content = soup.find("div", class_="cnt-main-body")

        if not main_content:
            print(f"Aucun contenu trouvé pour l'URL {url}.")
            return None  # Si aucun contenu n'est trouvé

        content = [p.get_text(strip=True) for p in main_content.find_all("p")]
        return "\n".join(content) if content else None  # Si le contenu est vide, retourner None

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de l'article {url} : {e}")
        return None  # Retourner None en cas d'erreur


def store_article_content(article_id, content):
    """Enregistrer le contenu de l'article dans la base de données seulement s'il y a du contenu."""
    if content is None:
        print(f"Aucun contenu pour l'article {article_id}, rien à enregistrer.")
        return  # Ne rien faire si le contenu est None

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Vérifier si l'article existe déjà dans la table
        cursor.execute("SELECT id FROM article_content WHERE article_id = %s", (article_id,))
        result = cursor.fetchone()

        if result:
            print(f"L'article {article_id} est déjà présent dans la base.")
        else:
            cursor.execute(
                "INSERT INTO article_content (article_id, content) VALUES (%s, %s)",
                (article_id, content)
            )
            connection.commit()
            print(f"Contenu de l'article {article_id} enregistré avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du contenu de l'article {article_id} : {e}")
    finally:
        cursor.close()
        connection.close()


def main():
    """Script principal pour récupérer et stocker le contenu des articles Digital Strategy."""
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT id, link FROM articles WHERE source = 'Digital Strategy'")
        articles = cursor.fetchall()

        for article in articles:
            article_id = article["id"]
            url = article["link"]
            print(f"Traitement de l'article {article_id} ({url})...")

            content = fetch_digital_strategy_content(url)
            if not content:
                print(f"Impossible de récupérer le contenu pour l'URL : {url}")
                continue  # Si le contenu est vide ou introuvable, on passe à l'article suivant

            store_article_content(article_id, content)
            time.sleep(2)  # Pause entre les requêtes pour éviter trop de requêtes rapides

        print("Traitement terminé.")
    except Exception as e:
        print(f"Erreur dans le script principal : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()

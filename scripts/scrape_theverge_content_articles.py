import os
import requests
from bs4 import BeautifulSoup
import mysql.connector
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


def fetch_theverge_content(url):
    try:
        # Envoyer une requête HTTP pour récupérer le contenu de la page
        response = requests.get(url)
        response.raise_for_status()  # Vérifier si la requête s'est bien passée
        
        # Parser le HTML de la page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Localiser les sections contenant le contenu de l'article
        # Adapter le sélecteur CSS au cas de "duet--article--article-body-component"
        article_sections = soup.find_all("div", class_="duet--article--article-body-component")
        
        # Initialiser une liste pour stocker le texte
        content = []
        
        # Extraire le texte de chaque paragraphe (<p>) dans chaque section
        for section in article_sections:
            paragraphs = section.find_all("p", class_="duet--article--dangerously-set-cms-markup")
            for paragraph in paragraphs:
                content.append(paragraph.get_text(strip=True))  # Nettoyage
        
        # Joindre tout le contenu extrait avec des sauts de ligne
        full_content = "\n".join(content)
        return full_content if full_content else "Aucun contenu trouvé."

    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la récupération de l'article : {e}"


def store_article_content(article_id, content):
    """
    Insère le contenu complet d'un article dans article_content
    uniquement s'il n'existe pas déjà.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Vérifier si l'article existe déjà dans la table
        cursor.execute("SELECT id FROM article_content WHERE article_id = %s",
                       (article_id,))
        result = cursor.fetchone()

        if result:
            print(f"L'article {article_id} est déjà présent dans la base.")
        else:
            # Insérer si pas encore présent
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
    """
    Script principal pour récupérer et stocker le contenu des articles The Verge.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sélectionner les articles The Verge dans la table articles
        cursor.execute("SELECT id, link FROM articles WHERE source = 'The Verge'")
        articles = cursor.fetchall()

        for article in articles:
            article_id = article["id"]
            url = article["link"]

            print(f"Traitement de l'article {article_id} ({url})...")

            # Récupérer le contenu
            content = fetch_theverge_content(url)
            if not content:
                print(f"Impossible de récupérer le contenu pour l'URL : {url}")
                continue

            # Enregistrer le contenu dans la table article_content
            store_article_content(article_id, content)

        print("Traitement terminé.")
    except Exception as e:
        print(f"Erreur dans le script principal : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()

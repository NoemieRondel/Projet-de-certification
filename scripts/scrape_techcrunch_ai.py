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


def fetch_techcrunch_content(url):
    """
    Récupérer le contenu complet d'un article TechCrunch.
    """
    try:
        # Envoyer une requête HTTP pour récupérer le contenu de la page
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Vérifier si la requête s'est bien passée

        # Parser le HTML de la page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Localiser le conteneur principal de l'article
        article_section = soup.find("div", class_="entry-content wp-block-post-content is-layout-constrained wp-block-post-content-is-layout-constrained")

        # Vérifier si le conteneur de l'article existe
        if not article_section:
            print(f"Aucun contenu trouvé pour l'URL : {url}")
            return None

        # Extraire le texte de chaque paragraphe
        content = []
        paragraphs = article_section.find_all("p")
        for paragraph in paragraphs:
            content.append(paragraph.get_text(strip=True))

        # Joindre le contenu extrait avec des sauts de ligne
        full_content = "\n".join(content)
        if full_content:
            print(f"Contenu récupéré pour {url} (extrait : {full_content[:100]}...)")
            return full_content
        else:
            print(f"Contenu vide pour l'URL : {url}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau pour {url} : {e}")
        return None


def update_article_content(article_id, full_content):
    """
    Met à jour le contenu complet d'un article dans la table `articles`.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Mettre à jour le champ `full_content` si vide
        cursor.execute(
            "UPDATE articles SET full_content = %s WHERE id = %s AND (full_content IS NULL OR full_content = '')",
            (full_content, article_id)
        )
        connection.commit()

        if cursor.rowcount > 0:
            print(f"Contenu de l'article {article_id} mis à jour avec succès.")
        else:
            print(f"L'article {article_id} a déjà un contenu ou n'existe pas.")

    except mysql.connector.Error as e:
        print(f"Erreur lors de la mise à jour de l'article {article_id} : {e}")
    finally:
        cursor.close()
        connection.close()


def main():
    """
    Script principal pour récupérer et mettre à jour le contenu des articles TechCrunch.
    """
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)

        # Sélectionner les articles TechCrunch dont le contenu complet est vide
        cursor.execute("SELECT id, link FROM articles WHERE source = 'TechCrunch' AND (full_content IS NULL OR full_content = '')")
        articles = cursor.fetchall()

        for article in articles:
            article_id = article["id"]
            url = article["link"]

            print(f"Traitement de l'article {article_id} ({url})...")

            # Récupérer le contenu complet de l'article
            full_content = fetch_techcrunch_content(url)
            if not full_content:
                print(f"Impossible de récupérer le contenu pour l'article {article_id}.")
                continue

            # Mettre à jour le contenu complet dans la table articles
            update_article_content(article_id, full_content)

        print("Traitement terminé.")
    except Exception as e:
        print(f"Erreur dans le script principal : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    main()

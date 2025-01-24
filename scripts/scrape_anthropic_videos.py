import os
import requests
import xml.etree.ElementTree as ET
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# URL du flux RSS
rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA"

# Chemin du dossier pour les fichiers de sortie
OUTPUT_DIR = "videos_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Crée le dossier s'il n'existe pas

# Fichier JSON pour stocker les vidéos
JSON_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "anthropic_videos.json")


def load_existing_data():
    """
    Charge les vidéos existantes à partir du fichier JSON.
    """
    if os.path.exists(JSON_OUTPUT_FILE):
        try:
            with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as json_file:
                logger.info("Chargement des vidéos existantes...")
                return json.load(json_file)
        except (IOError, json.JSONDecodeError):
            logger.warning("Erreur lors du chargement des vidéos existantes. Le fichier sera recréé.")
    return []


def save_data_to_json(data):
    """
    Sauvegarde les données dans un fichier JSON.
    """
    try:
        with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Données sauvegardées avec succès dans '{JSON_OUTPUT_FILE}'.")
    except IOError as e:
        logger.error(f"Erreur lors de l'écriture du fichier JSON : {e}")


def fetch_rss_feed():
    """
    Télécharge et parse le flux RSS.
    """
    try:
        logger.info(f"Téléchargement du flux RSS depuis {rss_url}...")
        response = requests.get(rss_url)
        response.raise_for_status()
        logger.info("Flux RSS téléchargé avec succès.")
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors du téléchargement du flux RSS : {e}")
        exit()


def process_videos(root, existing_urls):
    """
    Traite les vidéos du flux RSS et retourne une liste de nouvelles vidéos.
    """
    namespaces = {
        'media': 'http://search.yahoo.com/mrss/',
        'yt': 'http://www.youtube.com/xml/schemas/2015',
        'atom': 'http://www.w3.org/2005/Atom',
    }

    videos_data = []
    videos_added = 0

    # Parcourir les entrées du flux
    for entry in root.findall('atom:entry', namespaces):
        title = entry.find('atom:title', namespaces).text
        video_url = entry.find('atom:link', namespaces).attrib['href']
        published_date = entry.find('atom:published', namespaces).text
        channel_name = root.find('atom:title', namespaces).text
        channel_id = root.find('yt:channelId', namespaces).text

        # Extraire la description depuis media:description
        media_group = entry.find('media:group', namespaces)
        media_description = media_group.find(
            'media:description',
            namespaces).text if media_group is not None else None

        # Vérifier si l'URL de la vidéo existe déjà
        if video_url not in existing_urls:
            # Ajouter la vidéo à la liste des vidéos à enregistrer
            videos_data.append({
                "title": title,
                "source": "Anthropic",
                "publication_date": published_date,
                "video_url": video_url,
                "description": media_description,
                "channel_id": channel_id,
                "channel_name": channel_name
            })
            existing_urls.add(video_url)  # Ajouter l'URL à l'ensemble des existants
            videos_added += 1
            logger.info(f"Nouvelle vidéo ajoutée : {title}")

    logger.info(f"Nombre de nouvelles vidéos ajoutées : {videos_added}")
    return videos_data


def main():
    # Charger les vidéos existantes
    existing_data = load_existing_data()
    existing_urls = {video["video_url"] for video in existing_data}

    # Récupérer et traiter le flux RSS
    root = fetch_rss_feed()
    new_videos = process_videos(root, existing_urls)

    # Fusionner les nouvelles vidéos avec les données existantes
    existing_data.extend(new_videos)

    # Sauvegarder les données mises à jour
    save_data_to_json(existing_data)


if __name__ == "__main__":
    main()

import os
import requests
import xml.etree.ElementTree as ET
import json
import logging

# Initialisation de la configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL du flux RSS de la chaîne Google DeepMind
rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCP7jMXSY2xbc3KCAE0MHQ-A"

# Chemin du dossier pour les fichiers de sortie
OUTPUT_DIR = "videos_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fichier JSON pour stocker les vidéos collectées
JSON_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "google_deepmind_videos.json")

# Télécharger et charger le flux RSS
logging.info("Téléchargement du flux RSS...")
response = requests.get(rss_url)
if response.status_code != 200:
    logging.error(f"Erreur lors du téléchargement du flux RSS. Statut : {response.status_code}")
    exit()
logging.info("Flux RSS téléchargé avec succès.")

# Parser le flux XML pour en extraire les données
root = ET.fromstring(response.content)

# Espaces de noms XML pour manipuler les balises avec préfixes
namespaces = {
    'media': 'http://search.yahoo.com/mrss/',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'atom': 'http://www.w3.org/2005/Atom',
}

# Liste pour stocker les nouvelles vidéos à enregistrer
videos_data = []

# Charger les vidéos existantes à partir du fichier JSON (pour éviter les doublons)
logging.info(f"Vérification des vidéos existantes dans '{JSON_OUTPUT_FILE}'...")
if os.path.exists(JSON_OUTPUT_FILE):
    with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as json_file:
        existing_data = json.load(json_file)
else:
    existing_data = []
logging.info(f"Chargement des vidéos existantes terminé. Nombre d'éléments : {len(existing_data)}")

# Créer un ensemble des URLs existantes pour détecter les doublons
existing_urls = {video["video_url"] for video in existing_data}

videos_added = 0  # Compteur de nouvelles vidéos ajoutées

# Parcourir les entrées du flux RSS pour extraire les données des vidéos
logging.info("Traitement des vidéos dans le flux RSS...")
for entry in root.findall('atom:entry', namespaces):
    title = entry.find('atom:title', namespaces).text
    video_url = entry.find('atom:link', namespaces).attrib['href']
    published_date = entry.find('atom:published', namespaces).text
    channel_name = root.find('atom:title', namespaces).text
    channel_id = root.find('yt:channelId', namespaces).text

    # Extraire la description de la vidéo (si disponible)
    media_group = entry.find('media:group', namespaces)
    media_description = (
        media_group.find('media:description', namespaces).text
        if media_group is not None
        else None
    )

    # Vérifier si la vidéo est déjà dans les données existantes
    if video_url not in existing_urls:
        # Ajouter les informations de la vidéo à la liste
        videos_data.append({
            "title": title,
            "source": "Google DeepMind",
            "publication_date": published_date,
            "video_url": video_url,
            "description": media_description,
            "channel_id": channel_id,
            "channel_name": channel_name
        })
        existing_urls.add(video_url)
        videos_added += 1
        logging.info(f"Vidéo ajoutée : {title} ({video_url})")

# Fusionner les nouvelles vidéos avec les données existantes
logging.info(f"Fusion des vidéos nouvelles avec les existantes... Nombre total de vidéos : {len(existing_data) + len(videos_data)}")
existing_data.extend(videos_data)

# Sauvegarder les données mises à jour dans un fichier JSON
logging.info(f"Sauvegarde des vidéos dans '{JSON_OUTPUT_FILE}'...")
with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
    json.dump(existing_data, json_file, ensure_ascii=False, indent=4)
logging.info("Sauvegarde terminée.")

# Afficher le nombre de vidéos ajoutées
logging.info(f"{videos_added} vidéos ont été ajoutées au fichier JSON '{JSON_OUTPUT_FILE}'.")

import os
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import json

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# URL du flux RSS
rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC5-pBdfdA3KUo-vq72l-umA"

# Chemin du dossier pour les fichiers de sortie
OUTPUT_DIR = "videos_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Crée le dossier s'il n'existe pas

# Fichier JSON pour stocker les vidéos
JSON_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "mistral_videos.json")

# Charger le flux RSS
response = requests.get(rss_url)
if response.status_code != 200:
    print("Erreur lors du téléchargement du flux RSS.")
    exit()

# Parser le flux XML
root = ET.fromstring(response.content)

# Espaces de noms XML (pour accéder aux balises avec préfixes)
namespaces = {
    'media': 'http://search.yahoo.com/mrss/',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'atom': 'http://www.w3.org/2005/Atom',
}

videos_data = []  # Liste pour stocker les vidéos à enregistrer dans le fichier JSON

# Parcourir les entrées du flux
for entry in root.findall('atom:entry', namespaces):
    title = entry.find('atom:title', namespaces).text
    video_url = entry.find('atom:link', namespaces).attrib['href']
    published_date = entry.find('atom:published', namespaces).text
    channel_name = root.find('atom:title', namespaces).text
    channel_id = root.find('yt:channelId', namespaces).text

    # Extraire la description depuis media:description
    media_group = entry.find('media:group', namespaces)
    media_description = media_group.find('media:description', namespaces).text if media_group is not None else None

    # Ajouter la vidéo à la liste pour JSON si elle n'est pas déjà présente
    if not any(video['video_url'] == video_url for video in videos_data):
        videos_data.append({
            "title": title,
            "source": "Mistral AI",
            "publication_date": published_date,
            "video_url": video_url,
            "description": media_description,
            "channel_id": channel_id,
            "channel_name": channel_name
        })

# Sauvegarde des données dans un fichier JSON
if os.path.exists(JSON_OUTPUT_FILE):
    with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as json_file:
        existing_data = json.load(json_file)
else:
    existing_data = []

# Fusionner les nouvelles vidéos avec les données existantes (sans doublons)
existing_data.extend(videos_data)

with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
    json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

print(f"{len(videos_data)} vidéos ont été ajoutées ou mises à jour dans le fichier JSON '{JSON_OUTPUT_FILE}'.")

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
rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCP7jMXSY2xbc3KCAE0MHQ-A"


# Chemin du dossier pour les fichiers de sortie
OUTPUT_DIR = "videos_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fichier JSON pour stocker les vidéos
JSON_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "google_deepmind_videos.json")

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

# Liste pour stocker les vidéos à enregistrer dans le JSON
videos_data = []

# Charger les vidéos existantes à partir du fichier JSON (pour éviter les doublons)
if os.path.exists(JSON_OUTPUT_FILE):
    with open(JSON_OUTPUT_FILE, "r", encoding="utf-8") as json_file:
        existing_data = json.load(json_file)
else:
    existing_data = []

# Créer un set des URLs existantes pour une recherche rapide de doublons
existing_urls = {video["video_url"] for video in existing_data}

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
    media_description = media_group.find('media:description', namespaces).text if media_group is not None else None

    # Vérifier si l'URL de la vidéo existe déjà
    if video_url not in existing_urls:
        # Ajouter la vidéo à la liste des vidéos à enregistrer
        videos_data.append({
            "title": title,
            "source": "Google DeepMind",
            "publication_date": published_date,
            "video_url": video_url,
            "description": media_description,
            "channel_id": channel_id,
            "channel_name": channel_name
        })
        existing_urls.add(video_url)  # Ajouter l'URL à l'ensemble des existants
        videos_added += 1

# Fusionner les nouvelles vidéos avec les données existantes (si vous voulez que le fichier JSON garde tout)
existing_data.extend(videos_data)

# Sauvegarde des données dans un fichier JSON
with open(JSON_OUTPUT_FILE, "w", encoding="utf-8") as json_file:
    json.dump(existing_data, json_file, ensure_ascii=False, indent=4)

print(f"{videos_added} vidéos ont été ajoutées au fichier JSON '{JSON_OUTPUT_FILE}'.")
import os
import requests
import xml.etree.ElementTree as ET
import mysql.connector
from dotenv import load_dotenv

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
rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCrDwWp7EBBv4NwvScIpBDOA"

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

# Connexion à la base de données
connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()

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

    # Insertion ou mise à jour dans la base de données
    cursor.execute("""
        INSERT INTO videos (
            title,
            source,
            publication_date,
            video_url,
            description,
            channel_id,
            channel_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        publication_date = VALUES(publication_date),
        description = VALUES(description),
        source = VALUES(source)
    """, (
        title,
        "Anthropic",
        published_date,
        video_url,
        media_description,
        channel_id,
        channel_name))
    videos_added += cursor.rowcount

# Confirmer les modifications
connection.commit()
cursor.close()
connection.close()

print(f"{videos_added} vidéos ont été ajoutées ou mises à jour.")

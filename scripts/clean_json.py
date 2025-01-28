import os
import re
import json
import logging
from bs4 import BeautifulSoup

# Configuration simple du logging affiché dans le terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Liste de termes superflus à filtrer
noise_terms = [
    "click here", "read more", "terms and conditions", "privacy policy",
    "sign up", "subscribe", "learn more", "advertisement", "copyright",
    "all rights reserved", "powered by", "follow us", "get started"
]


def clean_text(text):
    """Nettoie un texte en supprimant les éléments inutiles."""
    if not text:
        return None

    # Suppression des balises HTML
    text = BeautifulSoup(text, "html.parser").get_text()

    # Suppression des termes superflus
    for term in noise_terms:
        text = re.sub(rf"\b{re.escape(term)}\b", "", text, flags=re.IGNORECASE)

    # Suppression des caractères spéciaux et des espaces multiples
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)  # Garder uniquement lettres, chiffres, espaces
    text = re.sub(r"\s+", " ", text)  # Réduction des espaces multiples à un seul

    return text


def clean_json_file(file_path, fields_to_clean):
    """Nettoie les champs textuels dans un fichier JSON donné."""
    modified_count = 0  # Compteur des modifications

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for entry in data:
            # Nettoyage des champs spécifiques à chaque fichier
            for field in fields_to_clean:
                if field in entry and entry[field]:
                    cleaned_text = clean_text(entry[field])
                    if cleaned_text != entry[field]:
                        entry[field] = cleaned_text
                        modified_count += 1
                        logging.info(f"Texte nettoyé pour l'ID {entry.get('id', 'inconnu')} dans le champ '{field}'.")

        # Réécriture du fichier avec les données nettoyées
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        logging.info(f"Nettoyage terminé pour le fichier '{file_path}'. Total des éléments modifiés : {modified_count}")

    except Exception as e:
        logging.error(f"Erreur lors du nettoyage du fichier {file_path} : {e}")


def clean_all_json_files():
    """Nettoie tous les fichiers JSON des articles, vidéos et arxiv_articles."""
    files_info = {
        "articles.json": ['summary', 'full_content'],
        "videos.json": ['description'],
        "arxiv_articles.json": ['abstract']
    }

    for json_file, fields_to_clean in files_info.items():
        file_path = os.path.join(os.getcwd(), json_file) # Remplacer par le chemin correct
        if os.path.exists(file_path):
            logging.info(f"Début du nettoyage pour le fichier : {json_file}")
            clean_json_file(file_path, fields_to_clean)
        else:
            logging.warning(f"Fichier non trouvé : {json_file}")


if __name__ == "__main__":
    clean_all_json_files()

import os
import json
import logging
import sys  # Import nécessaire pour utiliser sys.exit()

# Définir les chemins vers les dossiers des fichiers JSON
ARTICLES_FOLDER = "articles_outputs"
VIDEOS_FOLDER = "videos_outputs"

# Définir les chemins des fichiers JSON finaux
FINAL_ARTICLES_FILE = "articles.json"
FINAL_VIDEOS_FILE = "videos.json"

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def merge_and_deduplicate_json_files(input_folder, output_file, unique_key):
    all_data = []
    seen_keys = set()  # Ensemble pour stocker les clés uniques déjà rencontrées
    logging.info(f"Début du processus de fusion et dédoublonnage pour {input_folder}.")

    # Parcourir tous les fichiers JSON dans le dossier
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if file_name.endswith(".json"):
            try:
                # Charger les données JSON
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    # Vérifier que les données sont une liste
                    if isinstance(data, list):
                        logging.info(f"Traitement du fichier : {file_name}")
                        for item in data:
                            # Vérifier si la clé unique existe et est nouvelle
                            key_value = item.get(unique_key)
                            if key_value and key_value not in seen_keys:
                                all_data.append(item)
                                seen_keys.add(key_value)
                        logging.info(f"{len(data)} éléments traités dans {file_name}.")
                    else:
                        logging.warning(f"Le fichier {file_name} ne contient pas une liste. Ignoré.")
            except json.JSONDecodeError:
                logging.error(f"Erreur lors du chargement du fichier {file_name}. Ignoré.")

    # Sauvegarder les données fusionnées et dédoublonnées dans un nouveau fichier JSON
    try:
        with open(output_file, "w", encoding="utf-8") as output:
            json.dump(all_data, output, ensure_ascii=False, indent=4)
        logging.info(f"Fusion et dédoublonnage terminés. Les données ont été sauvegardées dans {output_file}.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du fichier {output_file}: {e}")
        if output_file == FINAL_ARTICLES_FILE:  # Vérifier si l'erreur concerne `articles.json`
            sys.exit(1)  # Arrêter l'exécution du workflow uniquement dans ce cas

# Fusionner et dédoublonner les fichiers JSON pour les articles
logging.info("Fusion et dédoublonnage des fichiers JSON pour les articles...")
merge_and_deduplicate_json_files(ARTICLES_FOLDER, FINAL_ARTICLES_FILE, unique_key="link")

# Fusionner et dédoublonner les fichiers JSON pour les vidéos
logging.info("Fusion et dédoublonnage des fichiers JSON pour les vidéos...")
merge_and_deduplicate_json_files(VIDEOS_FOLDER, FINAL_VIDEOS_FILE, unique_key="video_url")

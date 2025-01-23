import os
import json

# Définir les chemins vers les dossiers des fichiers JSON
ARTICLES_FOLDER = "articles_outputs"
VIDEOS_FOLDER = "videos_outputs"

# Définir les chemins des fichiers JSON finaux
FINAL_ARTICLES_FILE = "articles.json"
FINAL_VIDEOS_FILE = "videos.json"


def merge_and_deduplicate_json_files(input_folder, output_file, unique_key):
    all_data = []
    seen_keys = set()  # Ensemble pour stocker les clés uniques déjà rencontrées

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
                        for item in data:
                            # Vérifier si la clé unique existe et est nouvelle
                            key_value = item.get(unique_key)
                            if key_value and key_value not in seen_keys:
                                all_data.append(item)
                                seen_keys.add(key_value)
                    else:
                        print(f"Le fichier {file_name} ne contient pas une liste. Ignoré.")
            except json.JSONDecodeError:
                print(f"Erreur lors du chargement du fichier {file_name}. Ignoré.")

    # Sauvegarder les données fusionnées et dédoublonnées dans un nouveau fichier JSON
    with open(output_file, "w", encoding="utf-8") as output:
        json.dump(all_data, output, ensure_ascii=False, indent=4)

    print(f"Fusion et dédoublonnage terminés. Les données ont été sauvegardées dans {output_file}.")

# Fusionner et dédoublonner les fichiers JSON pour les articles
print("Fusion et dédoublonnage des fichiers JSON pour les articles...")
merge_and_deduplicate_json_files(ARTICLES_FOLDER, FINAL_ARTICLES_FILE, unique_key="link")

# Fusionner et dédoublonner les fichiers JSON pour les vidéos
print("Fusion et dédoublonnage des fichiers JSON pour les vidéos...")
merge_and_deduplicate_json_files(VIDEOS_FOLDER, FINAL_VIDEOS_FILE, unique_key="video_url")

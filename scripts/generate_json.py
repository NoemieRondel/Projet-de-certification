import os
import json

# Chemins vers les dossiers contenant les JSON
ARTICLES_FOLDER = "articles_output"
VIDEOS_FOLDER = "videos_output"

# Fichiers JSON finaux
FINAL_ARTICLES_JSON = "outputs/final_articles.json"
FINAL_VIDEOS_JSON = "outputs/final_videos.json"


def merge_json_files(input_folder, output_file):
    merged_data = []

    # Parcourir tous les fichiers JSON du dossier
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(input_folder, filename)
    
            try:
                # Charger les données JSON
                with open(file_path, "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        print(f"Le fichier {filename} ne contient pas une liste.")
            except Exception as e:
                print(f"Erreur lors du chargement de {filename} : {e}")
    
    # Écrire les données fusionnées dans le fichier final
    try:
        with open(output_file, "w", encoding="utf-8") as output_json:
            json.dump(merged_data, output_json, indent=4, ensure_ascii=False)
        print(f"Données fusionnées dans {output_file}.")
    except Exception as e:
        print(f"Erreur lors de l'écriture dans {output_file} : {e}")


# Fusion des articles
merge_json_files(ARTICLES_FOLDER, FINAL_ARTICLES_JSON)

# Fusion des vidéos
merge_json_files(VIDEOS_FOLDER, FINAL_VIDEOS_JSON)

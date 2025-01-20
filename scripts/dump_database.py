import os
from dotenv import load_dotenv
import subprocess

# Charger les variables d'environnement
load_dotenv()

# Récupérer les informations depuis le fichier .env
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")  # Récupérer le mot de passe
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

# Nom du fichier de dump (fixe pour écraser à chaque exécution)
dump_file = "sauvegarde_veille_ia.sql"

# Chemin absolu vers mysqldump (remplace si nécessaire)
mysqldump_path = r"C:\Program Files\MySQL\MySQL Workbench 8.0\mysqldump.exe"


def dump_database():
    """
    Effectue un dump de la base de données et écrase le fichier existant.
    """
    try:
        # Construire la commande mysqldump avec le mot de passe caché
        command = [
            mysqldump_path,
            f"-h{db_host}",
            f"-u{db_user}",
            f"--password={db_password}",  # Passe le mot de passe ici
            db_name
        ]

        # Ouvrir le fichier de dump pour écraser son contenu
        with open(dump_file, "w") as output_file:
            subprocess.run(command, stdout=output_file, check=True)

        print(f"Dump de la base de données terminé : {dump_file}")
        print("Ajoutez et committez le fichier dans votre dépôt Git pour versionner les changements.")

    except subprocess.CalledProcessError as e:
        print("Erreur lors de l'exécution de mysqldump :")
        print(e)

    except Exception as e:
        print("Erreur inattendue :")
        print(e)


if __name__ == "__main__":
    dump_database()

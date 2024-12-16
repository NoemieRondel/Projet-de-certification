import subprocess
import logging
import os
import sys

# Charger les variables d'environnement depuis le système
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Vérifier que toutes les variables sont disponibles
if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    print("Erreur : Certaines variables d'environnement nécessaires pour la base de données sont absentes.")
    sys.exit(1)

# Répertoire courant du script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Assurer que le dossier logs existe
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

# Configurer les logs
logging.basicConfig(
    filename=os.path.join(log_dir, 'scraping.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Liste des scripts à exécuter
SCRIPTS = [
    "scrape_aiwatch_eu.py",
    "scrape_anthropic_videos.py",
    "scrape_arxiv_ai.py",
    "scrape_azure_ai.py",
    "scrape_digital_strategy_eu_ai.py",
    "scrape_google_deepmind_videos.py",
    "scrape_microsoft_azure_videos.py",
    "scrape_mistral_videos.py",
    "scrape_mit_technology_review_ai.py",
    "scrape_openai_videos.py",
    "scrape_techcommunity_ai.py",
    "scrape_techcrunch_ai.py",
    "scrape_theverge_ai.py",
    "scrape_venturebeat_ai.py",
    "scrape_wired_ai.py",
]


def run_script(script_name):
    script_path = os.path.join(current_dir, script_name)
    try:
        # Passer les variables d'environnement nécessaires au script
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True,
            env=env  # Passer les variables d'environnement
        )
        logging.info(f"Script {script_name} exécuté avec succès.")
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'exécution de {script_name}: {e}")
        logging.error(e.stderr)
    except Exception as ex:
        logging.error(f"Erreur imprévue avec {script_name}: {ex}")


if __name__ == "__main__":
    # Assurer que le répertoire de travail est correct
    os.chdir(current_dir)

    for script in SCRIPTS:
        logging.info(f"Lancement du script : {script}")
        run_script(script)

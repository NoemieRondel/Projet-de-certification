import os
import sys
import subprocess

# Force l'utilisation de l'exécutable Python de l'environnement virtuel
sys.executable = r'C:\Users\NoémieRondel\OneDrive - talan.com\Certification\Projet final\Projet Veille IA\aimonitor\Scripts\python.exe'


def run_script(script_name):
    """
    Exécute un script Python donné et gère les erreurs.
    """
    try:
        print(f"=== Exécution de {script_name} ===")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"=== {script_name} terminé avec succès ===\n")
    except subprocess.CalledProcessError as e:
        print(f"!!! Erreur lors de l'exécution de {script_name}. Le processus est arrêté. !!!\n{e}")
        exit(1)


if __name__ == "__main__":
    # Change le répertoire de travail pour celui du script actuel
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("=== Début du pipeline de traitement des données ===\n")

    # Étape 1 : Intégration des JSON dans la base de données
    run_script("insert_json.py")

    # Étape 2 : Dump de la base de données
    run_script("dump_database.py")

    # Étape 3 : Nettoyage de la base de données
    run_script("database_cleanup.py")

    print("=== Pipeline de traitement des données terminé avec succès ===")

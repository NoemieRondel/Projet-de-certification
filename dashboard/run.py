import sys
import os
from dotenv import load_dotenv
from flask import session
from dashboard import create_app

# Charger les variables d'environnement depuis le fichier .env
load_dotenv(os.path.join(os.path.dirname(__file__), 'scripts', '.env'))

app = create_app()
app.secret_key = os.getenv("SECRET_KEY")  # Clé pour gérer les sessions

if __name__ == '__main__':
    app.run(debug=True)

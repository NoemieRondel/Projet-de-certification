from flask import Flask
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv(os.path.join(os.path.dirname(__file__), "../scripts/.env"))


# Fonction qui crée et initialise l'application Flask
def create_app():
    app = Flask(__name__)

    # Configurations de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY_DASHBOARD')
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Optionnel, pour formater les réponses JSON

    # Enregistrer les blueprints (routes) ici
    from .routes import main
    app.register_blueprint(main)

    return app

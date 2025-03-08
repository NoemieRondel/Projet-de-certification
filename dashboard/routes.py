import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import date

main = Blueprint("main", __name__)

API_URL = "http://127.0.0.1:8000"


def get_headers():
    """Retourne les headers avec le token d'authentification si l'utilisateur est connecté."""
    token = session.get("token")
    if not token:
        flash("Vous devez être connecté pour accéder à cette page.", "warning")
        return None
    return {"Authorization": f"Bearer {token}"}


def format_dates(data):
    """Convertit publication_date en string si elle est de type date."""
    if isinstance(data, list):  # Vérifie si c'est une liste d'objets
        for item in data:
            if "publication_date" in item and isinstance(item["publication_date"], date):
                item["publication_date"] = item["publication_date"].isoformat()  # Convertir en string
    elif isinstance(data, dict):  # Vérifie également le cas où data est un dictionnaire
        if "publication_date" in data and isinstance(data["publication_date"], date):
            data["publication_date"] = data["publication_date"].isoformat()  # Convertir en string
    return data


@main.route("/")
def home():
    """Page d'accueil - redirige vers le dashboard si connecté."""
    return redirect(url_for("main.dashboard")) if "token" in session else render_template("index.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    """Gère l'inscription des utilisateurs."""
    if request.method == "POST":
        username, email, password = request.form.get("username"), request.form.get("email"), request.form.get("password")
        response = requests.post(f"{API_URL}/auth/register", json={"username": username, "email": email, "password": password})

        if response.status_code == 200 and (token := response.json().get("access_token")):
            session["token"] = token
            return redirect(url_for("main.dashboard"))

        flash("Inscription échouée. Vérifiez vos informations.", "danger")

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    """Gère la connexion des utilisateurs."""
    if request.method == "POST":
        email, password = request.form.get("email"), request.form.get("password")
        response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})

        if response.status_code == 200 and (token := response.json().get("access_token")):
            session["token"] = token
            return redirect(url_for("main.dashboard"))

        flash("Identifiants incorrects.", "danger")

    return render_template("login.html")


@main.route("/logout")
def logout():
    """Déconnecte l'utilisateur."""
    session.pop("token", None)
    return redirect(url_for("main.login"))


@main.route("/dashboard")
def dashboard():
    """Affiche le tableau de bord si l'utilisateur est connecté."""
    return render_template("dashboard.html") if "token" in session else redirect(url_for("main.login"))


@main.route("/resources")
def resources():
    """Affiche les ressources avec la vidéo la plus récente pour chaque chaîne."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    resources_data = {"videos": [], "articles": [], "scientific_articles": []}

    try:
        # Récupérer toutes les vidéos disponibles
        response = requests.get(f"{API_URL}/videos", headers=headers)
        if response.status_code == 200:
            all_videos = format_dates(response.json())

            # Sélectionner la vidéo la plus récente par chaîne
            latest_videos = {}
            for video in all_videos:
                channel = video["channel_name"]
                if channel not in latest_videos or video["publication_date"] > latest_videos[channel]["publication_date"]:
                    latest_videos[channel] = video

            resources_data["videos"] = list(latest_videos.values())

        # Récupérer tous les articles disponibles
        response_articles = requests.get(f"{API_URL}/articles", headers=headers)
        if response_articles.status_code == 200:
            all_articles = format_dates(response_articles.json())

            # Sélectionner l'article le plus récent par source
            latest_articles = {}
            for article in all_articles:
                source = article["source"]  # Supposons que chaque article a un champ "source"
                if source not in latest_articles or article["publication_date"] > latest_articles[source]["publication_date"]:
                    latest_articles[source] = article

            resources_data["articles"] = list(latest_articles.values())

        # Récupérer les 5 derniers articles scientifiques
        response_scientific_articles = requests.get(f"{API_URL}/scientific-articles", headers=headers)
        if response_scientific_articles.status_code == 200:
            all_scientific_articles = format_dates(response_scientific_articles.json())

            # Trier par date de publication (en ordre décroissant)
            sorted_scientific_articles = sorted(all_scientific_articles, key=lambda x: x["publication_date"], reverse=True)

            # Récupérer les 5 derniers
            resources_data["scientific_articles"] = sorted_scientific_articles[:5]

    except requests.exceptions.RequestException:
        flash("Erreur de connexion au serveur.", "danger")

    return render_template("resources.html", resources=resources_data)


@main.route("/trends")
def trends():
    """Affiche les tendances des mots-clés avec filtres (dates et limite)."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    params = {
        "start_date": request.args.get("start_date", ""),
        "end_date": request.args.get("end_date", ""),
        "limit": request.args.get("limit", "10"),
    }

    try:
        response = requests.get(f"{API_URL}/trends/keywords", headers=headers, params=params)
        trends_data = response.json().get("trending_keywords", []) if response.status_code == 200 else []
    except Exception as e:
        flash(f"Erreur API : {str(e)}", "danger")
        trends_data = []

    return render_template("trends.html", trends=trends_data)

import requests
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import date, datetime

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
    """Convertit publication_date et timestamp en string si ce sont des objets date ou datetime."""
    fields = ["publication_date", "timestamp"]
    if isinstance(data, list):
        for item in data:
            for field in fields:
                if field in item and isinstance(item[field], (date, datetime)):
                    item[field] = item[field].isoformat()
    elif isinstance(data, dict):
        for field in fields:
            if field in data and isinstance(data[field], (date, datetime)):
                data[field] = data[field].isoformat()
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
    """Déconnecte l'utilisateur et invalide le token côté serveur si nécessaire."""
    headers = get_headers()

    if headers:  # Vérifier si l'utilisateur est bien connecté avant de tenter une requête
        try:
            requests.post(f"{API_URL}/auth/logout", headers=headers)  # Si l'API supporte une déconnexion
        except requests.exceptions.RequestException:
            flash("Erreur lors de la déconnexion côté serveur.", "warning")

    session.pop("token", None)
    flash("Vous avez été déconnecté avec succès.", "info")

    return render_template("index.html")


@main.route("/dashboard")
def dashboard():
    """Affiche le tableau de bord avec les tendances, métriques et derniers contenus."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    # Gestion des paramètres `limit` et `days_range`
    try:
        limit = int(request.args.get("limit", 10))
        if limit < 1 or limit > 50:
            raise ValueError
    except ValueError:
        flash("Le paramètre 'limit' doit être un entier entre 1 et 50.", "warning")
        limit = 10  # Valeur par défaut

    try:
        days_range = int(request.args.get("days_range", 90))  # Par défaut 90 jours
        if days_range < 7 or days_range > 365:
            raise ValueError
    except ValueError:
        flash("Le paramètre 'days_range' doit être un entier entre 7 et 365.", "warning")
        days_range = 90  # Valeur par défaut

    # Initialisation des données du tableau de bord
    dashboard_data = {
        "articles_by_source": [],
        "articles_by_keywords": [],
        "scientific_articles_by_keywords": [],
        "latest_videos": [],
        "trending_keywords": [],
        "articles_count": 0,
        "videos_count": 0,
        "scientific_articles_count": 0
    }

    # Fonction pour récupérer les données de l'API avec gestion des erreurs
    def fetch_api_data(endpoint):
        try:
            response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            flash(f"Erreur de connexion à {endpoint}: {str(e)}", "danger")
            return None

    # Récupération des données du dashboard
    dashboard_response = fetch_api_data(f"/dashboard?limit={limit}&days_range={days_range}")
    if dashboard_response:
        dashboard_data.update(dashboard_response)

        # Fusionner les articles de 'articles_by_source' et 'articles_by_keywords' en supprimant les doublons
        all_articles = dashboard_data["articles_by_source"] + dashboard_data["articles_by_keywords"]
        unique_articles = {article['link']: article for article in all_articles}  # Utiliser 'link' pour garantir l'unicité
        dashboard_data["unique_articles"] = list(unique_articles.values())  # Remplacer par la liste des articles uniques

        # Préparer les données pour le graphique des tendances
        trending_keywords_by_date = {}
        for entry in dashboard_data["trending_keywords"]:
            date = entry["date"]
            keywords = entry["keywords"]
            trending_keywords_by_date[date] = {kw["keyword"]: kw["count"] for kw in keywords}

        # Ajouter au contexte
        dashboard_data["trending_keywords_chart"] = trending_keywords_by_date

    return render_template("dashboard.html", dashboard=dashboard_data, limit=limit, days_range=days_range)


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
                channel = video["source"]
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
                source = article["source"]
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


@main.route("/search", methods=["GET", "POST"])
def search():
    """Page de recherche pour articles, vidéos et articles scientifiques."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    search_results = {"articles": [], "scientific_articles": [], "videos": []}

    if request.method == "POST":
        # Récupération des critères
        search_type = request.form.get("search_type")  # articles, scientific_articles ou videos
        source = request.form.get("source", "").strip()
        keywords = request.form.get("keywords", "").strip()
        authors = request.form.get("authors", "").strip()
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()

        params = {"keywords": keywords, "start_date": start_date, "end_date": end_date}

        try:
            if search_type == "articles":
                if source:
                    params["source"] = source
                response = requests.get(f"{API_URL}/articles", headers=headers, params=params)
                if response.status_code == 200:
                    search_results["articles"] = format_dates(response.json())

            elif search_type == "scientific_articles":
                if authors:
                    params["authors"] = authors
                response = requests.get(f"{API_URL}/scientific-articles", headers=headers, params=params)
                if response.status_code == 200:
                    search_results["scientific_articles"] = format_dates(response.json())

            elif search_type == "videos":
                if source:
                    params["source"] = source
                response = requests.get(f"{API_URL}/videos", headers=headers, params=params)
                if response.status_code == 200:
                    search_results["videos"] = format_dates(response.json())

        except requests.exceptions.RequestException:
            flash("Erreur de connexion au serveur.", "danger")

    return render_template("search.html", results=search_results)


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


@main.route("/metrics")
def metrics():
    """Affiche les métriques des articles, vidéos et mots-clés."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    metrics_data = {
        "articles_by_source": [],
        "videos_by_source": [],
        "top_keywords_by_source": [],
        "keyword_frequency": [],
        "scientific_keyword_frequency": [],
    }

    try:
        # Nombre d'articles par source
        response = requests.get(f"{API_URL}/metrics/articles-by-source", headers=headers)
        if response.status_code == 200:
            metrics_data["articles_by_source"] = response.json()

        # Nombre de vidéos par source
        response = requests.get(f"{API_URL}/metrics/videos-by-source", headers=headers)
        if response.status_code == 200:
            metrics_data["videos_by_source"] = response.json()

        # Fréquence des mots-clés dans les articles
        response = requests.get(f"{API_URL}/metrics/keyword-frequency", headers=headers)
        if response.status_code == 200:
            metrics_data["keyword_frequency"] = response.json()

        # Fréquence des mots-clés dans les articles scientifiques
        response = requests.get(f"{API_URL}/metrics/scientific-keyword-frequency", headers=headers)
        if response.status_code == 200:
            metrics_data["scientific_keyword_frequency"] = response.json()

        # Ajout des logs de monitoring
        response = requests.get(f"{API_URL}/metrics/monitoring-logs", headers=headers)
        if response.status_code == 200:
            metrics_data["monitoring_logs"] = response.json()

    except requests.exceptions.RequestException:
        flash("Erreur de connexion au serveur.", "danger")

    return render_template("metrics.html", metrics=metrics_data)


@main.route("/user_preferences", methods=["GET", "POST"])
def user_preferences():
    """Gère l'affichage, la modification et la suppression des préférences utilisateur."""
    headers = get_headers()
    if not headers:
        return redirect(url_for("main.login"))

    def fetch_data_from_api(url, headers, default_value=None):
        """Récupère les données depuis l'API et gère les erreurs."""
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                flash(f"Erreur lors de la récupération des données ({response.status_code})", "danger")
                return default_value
        except requests.exceptions.RequestException as e:
            flash(f"Erreur de connexion à {url}: {str(e)}", "danger")
            return default_value

    # Récupérer les filtres disponibles (sources, vidéos, mots-clés)
    filters_data = fetch_data_from_api(f"{API_URL}/preferences/user-preferences", headers, {"sources": [], "video_channels": [], "keywords": []})

    # Récupérer les préférences utilisateur
    user_prefs = fetch_data_from_api(f"{API_URL}/preferences/user-preferences", headers, {})

    if request.method == "POST":
        if "delete_action" in request.form:  # Détection d'une suppression via formulaire POST
            preferences_to_delete = {
                "source_preferences": request.form.getlist("source_preferences"),
                "video_channel_preferences": request.form.getlist("video_channel_preferences"),
                "keyword_preferences": request.form.getlist("keyword_preferences"),
            }

            try:
                response = requests.delete(
                    f"{API_URL}/preferences/user-preferences",
                    json=preferences_to_delete,
                    headers=headers
                )

                if response.status_code == 200:
                    flash("Préférences supprimées avec succès.", "success")
                else:
                    flash(f"Erreur lors de la suppression ({response.status_code})", "danger")
            except requests.exceptions.RequestException as e:
                flash(f"Erreur de connexion au serveur: {e}", "danger")

            return redirect(url_for("main.user_preferences"))

        else:  # Cas normal de mise à jour des préférences
            preferences_data = {
                "source_preferences": request.form.getlist("source_preferences"),
                "video_channel_preferences": request.form.getlist("video_channel_preferences"),
                "keyword_preferences": request.form.getlist("keyword_preferences"),
            }

            try:
                response = requests.post(f"{API_URL}/preferences/user-preferences", json=preferences_data, headers=headers)

                if response.status_code == 200:
                    flash("Préférences mises à jour avec succès.", "success")
                else:
                    flash(f"Erreur lors de la mise à jour ({response.status_code})", "danger")
            except requests.exceptions.RequestException:
                flash("Erreur de connexion au serveur.", "danger")

            return redirect(url_for("main.user_preferences"))

    return render_template(
        "user_preferences.html",
        preferences=user_prefs,
        filters=filters_data
    )


@main.route("/delete_account", methods=["DELETE"])
def delete_account():
    print("DELETE /delete_account appelé !")  # Ajoute un log
    headers = get_headers()
    if not headers:
        print("Aucun header trouvé !")
        flash("Vous devez être connecté pour supprimer votre compte.", "warning")
        return redirect(url_for("main.login"))

    try:
        response = requests.delete(f"{API_URL}/users/me", headers=headers)
        print("Requête envoyée à l'API, statut :", response.status_code)

        if response.status_code == 200:
            session.pop("token", None)
            flash("Votre compte a été supprimé avec succès.", "info")
            return redirect(url_for("main.home"), code=303)

        print("Erreur API :", response.text)
        flash("Erreur lors de la suppression du compte. Veuillez réessayer.", "danger")
    except requests.exceptions.RequestException as e:
        print("Erreur connexion API :", e)
        flash("Erreur de connexion au serveur. Veuillez réessayer.", "danger")

    return redirect(url_for("main.dashboard"))


@main.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Formulaire pour demander une réinitialisation de mot de passe."""
    if request.method == "POST":
        email = request.form.get("email")

        response = requests.post(f"{API_URL}/auth/forgot_password", json={"email": email})

        if response.status_code == 200:
            flash("Si cet email existe, un lien de réinitialisation a été envoyé.", "info")
        else:
            flash("Erreur lors de la demande de réinitialisation.", "danger")

    return render_template("forgot_password.html")


@main.route("/reset_password/<reset_token>", methods=["GET", "POST"])
def reset_password(reset_token):
    """Formulaire pour saisir un nouveau mot de passe après avoir cliqué sur le lien."""
    if request.method == "POST":
        new_password = request.form.get("password")

        response = requests.post(f"{API_URL}/auth/reset_password/{reset_token}", json={"new_password": new_password, "reset_token": reset_token})

        if response.status_code == 200:
            flash("Votre mot de passe a été réinitialisé avec succès.", "success")
            return redirect(url_for("main.login"))

        flash("Le lien est invalide ou expiré.", "danger")

    return render_template("reset_password.html", reset_token=reset_token)

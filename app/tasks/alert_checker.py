import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import get_connection


def check_preferences():
    """Vérifie les préférences des utilisateurs et récupère les articles et vidéos correspondants."""
    connection = get_connection()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Récupération des préférences des utilisateurs
                cursor.execute("SELECT * FROM user_preferences")
                user_preferences = cursor.fetchall()

                # Vérification des nouveaux articles et vidéos pour chaque utilisateur
                for user_pref in user_preferences:
                    user_id = user_pref['user_id']
                    source_preferences = user_pref['source_preferences']
                    video_channel_preferences = user_pref['video_channel_preferences']
                    keyword_preferences = user_pref['keyword_preferences']

                    # Vérification des nouveaux articles selon les préférences
                    check_articles(cursor, user_id, source_preferences, keyword_preferences)

                    # Vérification des nouvelles vidéos selon les préférences
                    check_videos(cursor, user_id, video_channel_preferences)

        except Exception as e:
            logging.error(f"Erreur lors de la vérification des préférences des utilisateurs : {str(e)}")
        finally:
            connection.close()


def check_articles(cursor, user_id, source_preferences, keyword_preferences):
    """Vérifie les nouveaux articles selon les préférences de l'utilisateur."""
    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if source_preferences:
        query += " AND source IN (%s)"
        params.append(source_preferences)

    if keyword_preferences:
        keyword_list = [f"%{kw.strip()}%" for kw in keyword_preferences.split(',')]
        query += " AND (" + " OR ".join(["keywords LIKE %s"] * len(keyword_list)) + ")"
        params.extend(keyword_list)

    cursor.execute(query, params)
    new_articles = cursor.fetchall()

    if new_articles:
        logging.info(f"Nouveaux articles pour l'utilisateur {user_id} : {len(new_articles)} nouveaux articles trouvés.")


def check_videos(cursor, user_id, video_channel_preferences):
    """Vérifie les nouvelles vidéos selon les préférences de l'utilisateur."""
    query = "SELECT * FROM videos WHERE 1=1"
    params = []

    if video_channel_preferences:
        query += " AND channel_name IN (%s)"
        params.append(video_channel_preferences)

    cursor.execute(query, params)
    new_videos = cursor.fetchall()

    if new_videos:
        logging.info(f"Nouvelles vidéos pour l'utilisateur {user_id} : {len(new_videos)} nouvelles vidéos trouvées.")


# Initialisation du scheduler pour exécuter la vérification toutes les 10 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(check_preferences, 'interval', minutes=10)
scheduler.start()

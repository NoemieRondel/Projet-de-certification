import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv(os.path.join(os.path.dirname(__file__), "../scripts/.env"))

# Charger les variables d'environnement
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "ton.email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "ton_mot_de_passe")
EMAIL_FROM = os.getenv("EMAIL_FROM", "ton.email@gmail.com")


def send_email(to_email: str, subject: str, body: str):
    """
    Envoie un email via SMTP.

    :param to_email: Email du destinataire
    :param subject: Sujet de l'email
    :param body: Contenu du message (HTML ou texte brut)
    """
    try:
        # Créer le message email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Connexion au serveur SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Sécuriser la connexion
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        # Envoyer l'email
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())

        # Fermer la connexion
        server.quit()
        print(f"Email envoyé à {to_email} avec succès.")

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

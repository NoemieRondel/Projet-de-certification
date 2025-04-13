from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_connection
from app.mailer import send_email
from contextlib import closing
import secrets
import datetime

router = APIRouter()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot_password")
def forgot_password(request: ForgotPasswordRequest):
    """Génère un token de réinitialisation et envoie un email."""

    email = request.email

    # Vérifier si l'email existe en base
    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}

        user_id = user["id"]

        # Générer un token sécurisé
        reset_token = secrets.token_urlsafe(32)

        # Stocker le token en base avec une expiration (1h)
        expiration_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE token=%s, expires_at=%s",
            (user_id, reset_token, expiration_time, reset_token, expiration_time)
        )
        conn.commit()

    # Construire le lien de réinitialisation
    reset_link = f"http://127.0.0.1:5000/reset_password/{reset_token}"

    # Envoyer l'email
    send_email(
        to_email=email,
        subject="Réinitialisation de votre mot de passe",
        body=f"Bonjour,\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe : {reset_link}\n\nCe lien expire dans 1 heure."
    )

    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}

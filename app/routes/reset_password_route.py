from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_connection
from contextlib import closing
import datetime
import bcrypt

router = APIRouter()


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/reset_password/{token}")
def reset_password(token: str, request: ResetPasswordRequest):
    """Réinitialise le mot de passe si le token est valide."""

    new_password = request.new_password

    # Vérifier le token en base
    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token = %s", (token,))
        token_data = cursor.fetchone()

        if not token_data:
            raise HTTPException(status_code=400, detail="Token invalide ou expiré")

        expires_at = token_data["expires_at"]
        user_id = token_data["user_id"]

        # Vérifier si le token est expiré
        if datetime.datetime.utcnow() > expires_at:
            cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
            conn.commit()
            raise HTTPException(status_code=400, detail="Token expiré")

        # Hacher le nouveau mot de passe
        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

        # Mettre à jour le mot de passe de l'utilisateur
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, user_id))

        # Supprimer le token après usage
        cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
        conn.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}

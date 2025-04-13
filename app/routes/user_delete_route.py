from fastapi import APIRouter, Depends, HTTPException
from app.database import get_connection
from app.security.jwt_handler import jwt_required
from contextlib import closing

router = APIRouter()


@router.delete("/me")
def delete_user_account(user=Depends(jwt_required)):
    """Supprime définitivement le compte utilisateur et ses préférences."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: user_id not found")

    with closing(get_connection()) as conn, conn.cursor(dictionary=True) as cursor:
        # Supprimer les préférences de l'utilisateur
        cursor.execute("DELETE FROM user_preferences WHERE user_id = %s", (user_id,))

        # Supprimer le compte utilisateur
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

        conn.commit()

    return {"message": "Votre compte a été supprimé avec succès."}

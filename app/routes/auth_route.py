from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_connection
from app.security.password_handler import hash_password, verify_password
from app.security.jwt_handler import create_access_token
from contextlib import closing

router = APIRouter()


# Modèles Pydantic pour validation
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/api/auth/register",
    summary="Inscription d'un nouvel utilisateur",
    response_model=AuthResponse,
    responses={
        200: {"description": "Inscription réussie"},
        400: {"description": "Email déjà utilisé"},
        500: {"description": "Erreur interne"}
    }
)
async def register_user(user: UserCreate):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email déjà utilisé.")

            hashed_password = hash_password(user.password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (user.username, user.email, hashed_password),
            )

            user_id = cursor.lastrowid
            connection.commit()

            token = create_access_token({"user_id": user_id})
            return {"access_token": token, "token_type": "bearer"}

        except HTTPException:
            raise

        except Exception as e:
            connection.rollback()
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


@router.post(
    "/api/auth/login",
    summary="Connexion utilisateur",
    response_model=AuthResponse,
    responses={
        200: {"description": "Connexion réussie"},
        401: {"description": "Identifiants invalides"},
        500: {"description": "Erreur interne"}
    }
)
async def login_user(user: UserLogin):
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", (user.username,))
            db_user = cursor.fetchone()

            if not db_user or not verify_password(user.password, db_user["password_hash"]):
                raise HTTPException(status_code=401, detail="Identifiants invalides.")

            token = create_access_token({"user_id": db_user["id"]})
            return {"access_token": token, "token_type": "bearer"}

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

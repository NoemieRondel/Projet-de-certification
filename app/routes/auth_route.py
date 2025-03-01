from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_connection
from app.security.password_handler import hash_password, verify_password
from app.security.jwt_handler import create_access_token
from contextlib import closing

router = APIRouter()


# Modèles Pydantic pour la validation
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str


# Inscription d'un utilisateur
@router.post(
    "/register",
    summary="Inscription d'un nouvel utilisateur",
    response_model=AuthResponse,
    responses={
        200: {"description": "Utilisateur inscrit avec succès."},
        400: {"description": "Email déjà utilisé."},
        500: {"description": "Erreur interne."}
    }
)
async def register_user(user: UserCreate):
    """Inscrit un nouvel utilisateur et génère un token immédiatement."""

    # Vérifier la connexion à la base de données
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor(dictionary=True)) as cursor:
        try:
            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email déjà utilisé.")

            # Hasher le mot de passe et insérer l'utilisateur
            hashed_password = hash_password(user.password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (user.username, user.email, hashed_password),
            )

            # Récupérer l'ID généré par MySQL
            user_id = cursor.lastrowid
            connection.commit()

            # Générer un token JWT après l'inscription
            token = create_access_token({"user_id": user_id})
            return {"access_token": token, "token_type": "bearer"}

        except Exception as e:
            connection.rollback()  # Annuler la transaction en cas d'erreur
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")


# Connexion d'un utilisateur
@router.post(
    "/login",
    summary="Connexion utilisateur",
    response_model=AuthResponse,
    responses={
        200: {"description": "Connexion réussie."},
        401: {"description": "Identifiants invalides."},
        500: {"description": "Erreur interne."}
    }
)
async def login_user(user: UserLogin):
    """Connecte un utilisateur et retourne un token JWT."""

    # Vérifier la connexion à la base de données
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor(dictionary=True)) as cursor:
        try:
            # Récupérer l'utilisateur en base
            cursor.execute("SELECT id, password_hash FROM users WHERE email = %s", (user.email,))
            db_user = cursor.fetchone()

            # Vérifier les identifiants
            if not db_user or not verify_password(user.password, db_user["password_hash"]):
                raise HTTPException(status_code=401, detail="Identifiants invalides.")

            # Générer un token JWT
            token = create_access_token({"user_id": db_user["id"]})
            return {"access_token": token, "token_type": "bearer"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

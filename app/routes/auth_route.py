from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.database import get_connection
from security.password_handler import hash_password, verify_password
from security.jwt_handler import create_access_token
from contextlib import closing

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", summary="Inscription d'un nouvel utilisateur")
async def register_user(user: UserCreate):
    """Inscrit un nouvel utilisateur avec un mot de passe sécurisé."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor()) as cursor:
        try:
            # Vérifier si l'email existe déjà
            cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email déjà utilisé.")

            # Hasher le mot de passe et insérer l'utilisateur
            hashed_password = hash_password(user.password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (user.username, user.email, hashed_password),
            )
            connection.commit()

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

    return {"message": "Utilisateur inscrit avec succès."}


@router.post("/login", summary="Connexion utilisateur")
async def login_user(user: UserLogin):
    """Connecte un utilisateur et retourne un token JWT."""
    connection = get_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Erreur de connexion à la base de données.")

    with closing(connection.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute(
                "SELECT id, password_hash FROM users WHERE email = %s",
                (user.email,)
            )
            db_user = cursor.fetchone()

            # Vérification des identifiants
            if not db_user or not verify_password(user.password, db_user["password_hash"]):
                raise HTTPException(status_code=401, detail="Identifiants invalides.")

            # Générer un token JWT
            token = create_access_token({"user_id": db_user["id"]})
            return {"access_token": token, "token_type": "bearer"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")

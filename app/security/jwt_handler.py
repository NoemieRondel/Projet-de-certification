from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer

# Charger les variables d'environnement
load_dotenv(os.path.join(os.path.dirname(__file__), "../scripts/.env"))

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict) -> str:
    """Génère un token JWT avec une expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "sub": data.get("sub")})  # Exemple: "sub" pour l'ID de l'utilisateur
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Vérifie la validité d'un token JWT et gère les erreurs spécifiques."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=403, detail=f"Token verification failed: {str(e)}")


async def jwt_required(token: str = Depends(oauth2_scheme)):
    """Vérifie le token JWT et retourne son payload."""
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    return verify_access_token(token)

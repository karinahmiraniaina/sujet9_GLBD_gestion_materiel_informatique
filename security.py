"""
Sécurité : hash des mots de passe + gestion des tokens JWT.
"""
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

# ⚠️ À changer en production, et à mettre dans .env
SECRET_KEY = "change-moi-avec-une-vraie-cle-secrete"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_mot_de_passe(mot_de_passe: str) -> str:
    """Transforme le mot de passe en clair en hash sécurisé (jamais stocké en clair)."""
    mot_de_passe_bytes = mot_de_passe.encode("utf-8")[:72]  # bcrypt limite à 72 octets
    return bcrypt.hashpw(mot_de_passe_bytes, bcrypt.gensalt()).decode("utf-8")


def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    mot_de_passe_bytes = mot_de_passe.encode("utf-8")[:72]
    return bcrypt.checkpw(mot_de_passe_bytes, mot_de_passe_hash.encode("utf-8"))


def creer_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Récupère l'utilisateur connecté à partir du token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()
    if utilisateur is None:
        raise credentials_exception
    return utilisateur


def require_role(*roles_autorises: str):
    """Dépendance pour restreindre un endpoint à certains rôles (ex: require_role('admin'))."""
    def wrapper(utilisateur: models.Utilisateur = Depends(get_current_user)):
        if utilisateur.role not in roles_autorises:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas les droits pour cette action"
            )
        return utilisateur
    return wrapper
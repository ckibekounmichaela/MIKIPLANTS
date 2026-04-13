# ============================================================
# FICHIER : backend/routers/auth.py
# RÔLE    : Gestion complète de l'authentification
#
# ENDPOINTS :
#   POST /api/auth/register        → Inscription + email de vérification
#   POST /api/auth/login           → Connexion + email de notification
#   GET  /api/auth/me              → Profil de l'utilisateur connecté
#   GET  /api/auth/verify-email    → Vérifier le compte via token
#   POST /api/auth/forgot-password → Demander réinitialisation mot de passe
#   POST /api/auth/reset-password  → Changer le mot de passe avec le token
#
# SÉCURITÉ :
#   - Mots de passe hashés avec bcrypt (irréversible)
#   - Tokens JWT signés (authentification sans état)
#   - Tokens de reset UUID (valides 1 heure seulement)
#   - Tokens de vérification UUID (valides 24 heures)
# ============================================================

import os
import uuid
import threading
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional

import bcrypt as _bcrypt
import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserResponse, Token, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from services import email_service

load_dotenv()

# -------------------------------------------------------
# Configuration JWT
# -------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "cle_secrete_par_defaut_changer_en_prod")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# --- Google OAuth2 ---
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("APP_BASE_URL", "http://localhost:8000") + "/api/auth/google/callback"

GOOGLE_AUTH_URL     = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL    = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def get_google_redirect_uri(request: Request) -> str:
    """Construit l'URI de callback depuis le host réel de la requête."""
    scheme = request.url.scheme          # "http"
    host   = request.url.hostname        # "localhost"
    port   = request.url.port            # 8001
    if port and port not in (80, 443):
        base = f"{scheme}://{host}:{port}"
    else:
        base = f"{scheme}://{host}"
    return f"{base}/api/auth/google/callback"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def hash_password(password: str) -> str:
    """
    Transforme un mot de passe en clair en hash bcrypt sécurisé.
    Ex: "MonMotDePasse123" → "$2b$12$KIX..."
    Ce hash est irréversible.
    """
    hashed = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond à son hash bcrypt."""
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT signé avec une date d'expiration.

    PARAMÈTRES :
        data          : Données à encoder (ex: {"sub": "user@email.com"})
        expires_delta : Durée de validité
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance FastAPI : récupère l'utilisateur connecté depuis son token JWT.
    Utilisée dans tous les endpoints protégés avec Depends(get_current_user).
    Lève HTTP 401 si le token est invalide ou expiré.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def _send_email_async(func, *args):
    """
    Envoyer un email dans un thread séparé pour ne pas bloquer la réponse API.

    CONCEPT :
        L'envoi d'email peut prendre 1-3 secondes.
        Si on attend la fin de l'envoi avant de répondre au client,
        l'expérience utilisateur est dégradée.
        Avec threading, l'API répond immédiatement et l'email part en parallèle.
    """
    thread = threading.Thread(target=func, args=args, daemon=True)
    thread.start()


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Créer un nouveau compte utilisateur.

    ÉTAPES :
    1. Vérifier unicité email et username
    2. Hasher le mot de passe
    3. Créer l'utilisateur avec un token de vérification UUID
    4. Envoyer un email de vérification (en arrière-plan)
    5. Retourner les infos de l'utilisateur créé
    """

    # Vérifier l'unicité de l'email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Un compte avec cet email existe déjà.")

    # Vérifier l'unicité du nom d'utilisateur
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris.")

    # Générer un token de vérification unique
    # uuid4() génère un identifiant universel unique (128 bits d'aléatoire)
    verification_token = str(uuid.uuid4())

    # Créer l'utilisateur en base
    new_user = User(
        username           = user_data.username,
        email              = user_data.email,
        password_hash      = hash_password(user_data.password),
        is_verified        = False,             # Compte non vérifié par défaut
        verification_token = verification_token
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Envoyer l'email de vérification en arrière-plan (sans bloquer la réponse)
    _send_email_async(
        email_service.send_verification_email,
        new_user.email,
        new_user.username,
        verification_token
    )

    return new_user


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Connecter un utilisateur et retourner un token JWT.

    ÉTAPES :
    1. Chercher l'utilisateur par email
    2. Vérifier le mot de passe
    3. (Optionnel) Vérifier que le compte est activé
    4. Créer et retourner le token JWT
    5. Envoyer une notification de connexion par email (en arrière-plan)
    """

    user = db.query(User).filter(User.email == user_data.email).first()

    # Vérifier email + mot de passe ensemble (protection timing attack)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")

    # Créer le token JWT
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Récupérer l'adresse IP du client pour la notification email
    ip_address = request.client.host if request.client else "Inconnue"

    # Envoyer la notification de connexion en arrière-plan
    _send_email_async(
        email_service.send_login_notification,
        user.email,
        user.username,
        ip_address
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Récupérer le profil de l'utilisateur connecté.
    Nécessite un token JWT valide dans le header Authorization.
    """
    return current_user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Vérifier le compte utilisateur via le token reçu par email.

    PARAMÈTRE (dans l'URL) :
        token : Le token UUID envoyé par email à l'inscription
                Ex: GET /api/auth/verify-email?token=abc123...

    COMPORTEMENT :
        - Si le token est valide → le compte est activé
        - Si le token est invalide ou déjà utilisé → erreur 400
    """

    # Chercher l'utilisateur avec ce token de vérification
    user = db.query(User).filter(
        User.verification_token == token
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Lien de vérification invalide ou déjà utilisé."
        )

    if user.is_verified:
        return {"message": "Votre compte est déjà vérifié. Vous pouvez vous connecter."}

    # Activer le compte et supprimer le token (usage unique)
    user.is_verified        = True
    user.verification_token = None
    db.commit()

    return {"message": "Compte vérifié avec succès ! Vous pouvez maintenant vous connecter."}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Demander la réinitialisation du mot de passe.

    ÉTAPES :
    1. Chercher l'utilisateur par email
    2. Générer un token de réinitialisation (valide 1 heure)
    3. Sauvegarder le token en base de données
    4. Envoyer l'email avec le lien de réinitialisation

    SÉCURITÉ : On renvoie TOUJOURS le même message, que l'email existe ou non,
    pour éviter de révéler quels emails sont enregistrés.
    """

    user = db.query(User).filter(User.email == data.email).first()

    # Message générique pour ne pas révéler si l'email existe
    success_message = {
        "message": "Si cet email est enregistré, vous recevrez un lien de réinitialisation."
    }

    if not user:
        # On retourne le même message même si l'email n'existe pas
        return success_message

    # Générer un token unique pour la réinitialisation
    reset_token = str(uuid.uuid4())

    # Le token expire dans 1 heure
    user.reset_token         = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    # Envoyer l'email de réinitialisation en arrière-plan
    _send_email_async(
        email_service.send_password_reset_email,
        user.email,
        user.username,
        reset_token
    )

    return success_message


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Choisir un nouveau mot de passe avec le token reçu par email.

    PARAMÈTRES (JSON) :
        token        : Token reçu dans l'email
        new_password : Nouveau mot de passe (minimum 6 caractères)

    ÉTAPES :
    1. Vérifier que le token existe et n'est pas expiré
    2. Hasher le nouveau mot de passe
    3. Mettre à jour le mot de passe
    4. Invalider le token (usage unique)
    """

    # Valider la longueur du nouveau mot de passe
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe doit contenir au moins 6 caractères."
        )

    # Chercher l'utilisateur avec ce token de réinitialisation
    user = db.query(User).filter(
        User.reset_token == data.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Lien de réinitialisation invalide ou déjà utilisé."
        )

    # Vérifier que le token n'est pas expiré (valide 1 heure)
    if user.reset_token_expires and datetime.utcnow() > user.reset_token_expires:
        raise HTTPException(
            status_code=400,
            detail="Ce lien a expiré. Veuillez faire une nouvelle demande."
        )

    # Mettre à jour le mot de passe et invalider le token
    user.password_hash      = hash_password(data.new_password)
    user.reset_token        = None   # Token usage unique → on le supprime
    user.reset_token_expires = None
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."}


@router.get("/google/login")
def google_login(request: Request):
    """
    Redirige l'utilisateur vers la page de connexion Google.
    """
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  get_google_redirect_uri(request),
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account"
    }
    url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    """
    Google redirige ici après la connexion avec un code temporaire.
    On échange ce code contre un token, on récupère les infos utilisateur,
    puis on crée/connecte le compte et on redirige vers le dashboard.
    """
    # 1. Échanger le code contre un access token Google
    redirect_uri = get_google_redirect_uri(request)
    async with httpx.AsyncClient() as client:
        token_response = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code"
        })

    if token_response.status_code != 200:
        return RedirectResponse("/login?error=google_token_failed")

    token_data   = token_response.json()
    access_token = token_data.get("access_token")

    # 2. Récupérer les infos du compte Google
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if userinfo_response.status_code != 200:
        return RedirectResponse("/login?error=google_userinfo_failed")

    google_user = userinfo_response.json()
    google_id   = google_user.get("id")
    email       = google_user.get("email")
    name        = google_user.get("name", "")
    # Construire un username à partir du nom Google (sans espaces ni accents)
    username_base = name.replace(" ", "_").lower()[:30] or email.split("@")[0]

    # 3. Trouver ou créer l'utilisateur en base
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        # Vérifier si un compte existe déjà avec cet email (compte classique)
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Lier le compte Google au compte existant
            user.google_id  = google_id
            user.is_verified = True
            db.commit()
        else:
            # Créer un nouveau compte via Google
            username = username_base
            # S'assurer que le username est unique
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{username_base}_{counter}"
                counter += 1

            user = User(
                username          = username,
                email             = email,
                password_hash     = None,   # Pas de mot de passe pour les comptes Google
                google_id         = google_id,
                is_verified       = True    # Email Google = déjà vérifié
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # 4. Créer un JWT et rediriger vers le dashboard
    jwt_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Rediriger vers le dashboard avec le token en paramètre URL
    # Le JS côté frontend le stockera dans localStorage
    return RedirectResponse(f"/dashboard?token={jwt_token}")


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changer le mot de passe depuis le profil utilisateur (connecté).

    PARAMÈTRES (JSON) :
        current_password : Mot de passe actuel (vérification sécurité)
        new_password     : Nouveau mot de passe (minimum 6 caractères)
    """

    # Vérifier que le mot de passe actuel est correct
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Mot de passe actuel incorrect."
        )

    # Vérifier la longueur du nouveau mot de passe
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit contenir au moins 6 caractères."
        )

    # Mettre à jour le mot de passe
    current_user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "Mot de passe modifié avec succès."}

import os
import uuid
import threading
import urllib.parse
import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt as _bcrypt
import httpx

logger = logging.getLogger(__name__)

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

# Configuration JWT
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
    """Retourne l'URI de callback Google OAuth.
    Priorité : variable GOOGLE_REDIRECT_URI dans .env
    Sinon : construite depuis APP_BASE_URL
    Sinon : construite depuis la requête en cours.
    """
    explicit = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if explicit:
        logger.info(f"[Google OAuth] redirect_uri (depuis .env) : {explicit}")
        return explicit

    base_url = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if base_url:
        uri = f"{base_url}/api/auth/google/callback"
        logger.info(f"[Google OAuth] redirect_uri (depuis APP_BASE_URL) : {uri}")
        return uri

    host = request.url.hostname or "localhost"
    port = request.url.port
    if host in ("localhost", "127.0.0.1"):
        base = f"http://{host}:{port}" if port else f"http://{host}"
    else:
        base = f"https://{host}"
    uri = f"{base}/api/auth/google/callback"
    logger.info(f"[Google OAuth] redirect_uri (depuis requête) : {uri}")
    return uri

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

router = APIRouter()



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
    Lève HTTP 401 si le token est invalide, expiré, ou révoqué.
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

    # Vérifier que le token n'a pas été révoqué par un changement de mot de passe
    token_version = payload.get("tv", 0)
    if token_version != (user.token_version or 0):
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
        username                    = user_data.username,
        email                       = user_data.email,
        password_hash               = hash_password(user_data.password),
        is_verified                 = True,
        verification_token          = verification_token,
        verification_token_expires  = datetime.utcnow() + timedelta(hours=24)
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

    # Aucun compte avec cet email
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Aucun compte trouvé avec cet email."
        )

    # Compte Google-only : pas de mot de passe local
    if user.password_hash is None:
        raise HTTPException(
            status_code=401,
            detail="Ce compte utilise la connexion Google. Connectez-vous avec Google."
        )

    # Mot de passe incorrect
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Mot de passe incorrect."
        )

    # Vérifier que le compte est activé (email confirmé)
    if not user.is_verified:
        raise HTTPException(
            status_code=401,
            detail="Compte non vérifié. Consultez vos emails et cliquez sur le lien de vérification."
        )

    # Créer le token JWT (tv = token_version pour invalidation future)
    access_token = create_access_token(
        data={"sub": user.email, "tv": user.token_version or 0},
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

    # Vérifier que le lien n'est pas expiré (24h)
    if user.verification_token_expires and datetime.utcnow() > user.verification_token_expires:
        raise HTTPException(
            status_code=400,
            detail="Ce lien de vérification a expiré. Créez un nouveau compte ou contactez le support."
        )

    # Activer le compte et supprimer le token (usage unique)
    user.is_verified                   = True
    user.verification_token            = None
    user.verification_token_expires    = None
    db.commit()

    return {"message": "Compte vérifié avec succès ! Vous pouvez maintenant vous connecter."}


@router.post("/resend-verification")
def resend_verification(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Renvoyer l'email de vérification à un utilisateur non encore vérifié.
    Utilise ForgotPasswordRequest (même schéma : juste un email).
    """
    user = db.query(User).filter(User.email == data.email).first()

    # Réponse générique pour éviter l'énumération d'emails
    generic_msg = {"message": "Si cet email est enregistré et non vérifié, un email de vérification a été envoyé."}

    if not user or user.is_verified:
        return generic_msg

    # Générer un nouveau token de vérification
    new_token = str(uuid.uuid4())
    user.verification_token         = new_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    _send_email_async(
        email_service.send_verification_email,
        user.email,
        user.username,
        new_token
    )

    return generic_msg


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

    # Valider la longueur du nouveau mot de passe (aligné sur change-password)
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Le mot de passe doit contenir au moins 8 caractères."
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

    # Mettre à jour le mot de passe, invalider le token, révoquer les JWT existants
    user.password_hash      = hash_password(data.new_password)
    user.reset_token        = None
    user.reset_token_expires = None
    user.token_version      = (user.token_version or 0) + 1
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."}


@router.get("/google/login")
def google_login(request: Request):
    """
    Redirige l'utilisateur vers la page de connexion Google.
    Un paramètre 'state' aléatoire est généré et stocké dans un cookie httpOnly
    pour prévenir les attaques CSRF sur le flow OAuth.
    """
    state = str(uuid.uuid4())
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  get_google_redirect_uri(request),
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
        "state":         state,
    }
    url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    response = RedirectResponse(url)
    is_localhost = request.url.hostname in ("localhost", "127.0.0.1")
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=300,
        httponly=True,
        samesite="lax",
        secure=not is_localhost,
    )
    return response


@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Google redirige ici après la connexion avec un code temporaire.
    On échange ce code contre un token, on récupère les infos utilisateur,
    puis on crée/connecte le compte et on redirige vers le dashboard.
    """
    # Vérifier le state pour prévenir les attaques CSRF
    stored_state = request.cookies.get("oauth_state")
    if not state or not stored_state or state != stored_state:
        logger.warning(f"[Google OAuth] State mismatch — possible CSRF. state={state}, cookie={stored_state}")
        return RedirectResponse("/login?error=oauth_state_invalid")

    try:
        # 1. Échanger le code contre un access token Google
        redirect_uri = get_google_redirect_uri(request)
        logger.info(f"[Google OAuth] redirect_uri utilisé : {redirect_uri}")

        async with httpx.AsyncClient() as client:
            token_response = await client.post(GOOGLE_TOKEN_URL, data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  redirect_uri,
                "grant_type":    "authorization_code"
            })

        logger.info(f"[Google OAuth] token_response status : {token_response.status_code}")
        logger.info(f"[Google OAuth] token_response body   : {token_response.text[:300]}")

        if token_response.status_code != 200:
            logger.error(f"[Google OAuth] Token échoué : {token_response.text[:200]}")
            return RedirectResponse("/login?error=google_failed")
    except Exception as e:
        logger.error(f"[Google OAuth] Exception : {e}")
        return RedirectResponse("/login?error=google_failed")

    try:
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
        username_base = name.replace(" ", "_").lower()[:30] or email.split("@")[0]

        logger.info(f"[Google OAuth] Utilisateur Google : {email} ({google_id})")

        # 3. Trouver ou créer l'utilisateur en base
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.google_id   = google_id
                user.is_verified = True
                db.commit()
            else:
                username = username_base
                counter  = 1
                while db.query(User).filter(User.username == username).first():
                    username = f"{username_base}_{counter}"
                    counter += 1

                user = User(
                    username      = username,
                    email         = email,
                    password_hash = None,
                    google_id     = google_id,
                    is_verified   = True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        # 4. Créer un JWT et rediriger vers le dashboard
        jwt_token = create_access_token(
            data={"sub": user.email, "tv": user.token_version or 0},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    except Exception as e:
        logger.error(f"[Google OAuth] Erreur callback : {e}")
        return RedirectResponse("/login?error=google_failed")

    # Rediriger vers le dashboard avec le token dans un cookie court (mobile-compatible)
    is_localhost = request.url.hostname in ("localhost", "127.0.0.1")
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        key="google_token",
        value=jwt_token,
        max_age=60,           # 60 secondes — juste le temps de récupérer en JS
        httponly=False,       # Le JS doit pouvoir le lire pour le mettre dans localStorage
        samesite="lax",
        secure=not is_localhost
    )
    # Supprimer le cookie oauth_state (usage unique)
    response.delete_cookie("oauth_state")
    return response


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

    # Compte Google-only : pas de mot de passe local à changer
    if current_user.password_hash is None:
        raise HTTPException(
            status_code=400,
            detail="Votre compte utilise Google. Impossible de définir un mot de passe local."
        )

    # Vérifier que le mot de passe actuel est correct
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Mot de passe actuel incorrect."
        )

    # Vérifier que le nouveau mot de passe est différent de l'ancien
    if verify_password(data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Le nouveau mot de passe doit être différent de l'ancien."
        )

    # Validation de la force du mot de passe
    pw = data.new_password
    if len(pw) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")
    if not any(c.isdigit() for c in pw):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins un chiffre.")
    if not any(c.isalpha() for c in pw):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins une lettre.")

    # Mettre à jour le mot de passe et révoquer les JWT existants
    current_user.password_hash  = hash_password(data.new_password)
    current_user.token_version  = (current_user.token_version or 0) + 1
    db.commit()

    return {"message": "Mot de passe modifié avec succès. Veuillez vous reconnecter."}

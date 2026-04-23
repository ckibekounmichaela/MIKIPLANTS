import os
import time
import collections
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))   # .../backend
ROOT_DIR     = os.path.dirname(BASE_DIR)                     # .../MIKIPLANTS
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
UPLOADS_DIR  = os.path.join(ROOT_DIR, "uploads")

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import engine, Base

from routers import auth, scan, chat, analytics, plants


try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tables créées / vérifiées avec succès.")
except Exception as e:
    logger.error(f"Erreur lors de la création des tables : {e}")
    logger.warning("L'app démarre quand même — vérifie DATABASE_URL et la connexion SSL.")

from sqlalchemy import text, inspect
try:
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns   = [c["name"] for c in inspector.get_columns("users")]

        if "google_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(100) NULL"))
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT uq_users_google_id UNIQUE (google_id)"))
            conn.commit()
            logger.info("Migration : colonne google_id ajoutée.")

        if "password_hash" in columns:
            is_postgres = str(engine.url).startswith("postgresql")
            if is_postgres:
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
            else:
                conn.execute(text("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(200) NULL"))
            conn.commit()
            logger.info("Migration : password_hash rendu nullable.")

        if "verification_token_expires" not in columns:
            is_postgres = str(engine.url).startswith("postgresql")
            col_type = "TIMESTAMP" if is_postgres else "DATETIME"
            conn.execute(text(f"ALTER TABLE users ADD COLUMN verification_token_expires {col_type} NULL"))
            conn.commit()
            logger.info("Migration : colonne verification_token_expires ajoutée.")

        if "token_version" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN token_version INT NOT NULL DEFAULT 0"))
            conn.commit()
            logger.info("Migration : colonne token_version ajoutée.")

except Exception as e:
    logger.warning(f"Migration optionnelle échouée (peut être déjà appliquée) : {e}")

try:
    with engine.connect() as conn:
        is_pg = str(engine.url).startswith("postgresql")
        indexes = [
            ("idx_scans_user_id",          "CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id)"),
            ("idx_scans_created_at",        "CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at)"),
            ("idx_plants_scientific_name",  "CREATE INDEX IF NOT EXISTS idx_plants_scientific_name ON plants(scientific_name)"),
        ]
        for idx_name, stmt in indexes:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  

        scan_cols = [c["name"] for c in inspector.get_columns("scans")]
        if "deleted_at" not in scan_cols:
            is_pg = str(engine.url).startswith("postgresql")
            col_type = "TIMESTAMP" if is_pg else "DATETIME"
            conn.execute(text(f"ALTER TABLE scans ADD COLUMN deleted_at {col_type} NULL DEFAULT NULL"))
            conn.commit()
            logger.info("Migration : colonne deleted_at ajoutée à scans.")

except Exception as e:
    logger.warning(f"Migration optionnelle échouée (peut être déjà appliquée) : {e}")


os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(
    title="MikiPlants API",
    description="""
    ## API d'analyse intelligente de plantes

    Prenez une photo d'une plante et obtenez instantanément :
    - ✅ L'identification de la plante
    - 🌿 Son état de santé
    - 🍽️ Sa comestibilité et des recettes
    - 💊 Ses propriétés médicinales
    - ⚠️ Sa toxicité et premiers secours
    - 🌍 Son impact environnemental
    """,
    version="1.0.0"
)


_rate_limit_store: dict = collections.defaultdict(list)

RATE_RULES = {
    "/api/auth/":         (10, 60),   # 10 req/min — anti brute-force
    "/api/scan/analyze":  (5,  60),   # 5 analyses/min — protège quota PlantNet+Groq
}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()

    for prefix, (max_req, window) in RATE_RULES.items():
        path_matches = request.url.path.startswith(prefix)
        method_ok    = request.method == "POST" if prefix == "/api/auth/" else True
        if path_matches and method_ok:
            key = f"{ip}:{prefix}"
            _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < window]
            if len(_rate_limit_store[key]) >= max_req:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Trop de requêtes. Réessayez dans une minute."}
                )
            _rate_limit_store[key].append(now)
            break

    return await call_next(request)



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.warning(f"[422] Validation échouée sur {request.method} {request.url.path}")
    logger.warning(f"[422] Body reçu : {body.decode('utf-8', errors='replace')}")
    logger.warning(f"[422] Erreurs   : {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})



_app_base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
_cors_origins  = [_app_base_url] if _app_base_url else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentification"]   # Groupe dans la documentation /docs
)

app.include_router(
    scan.router,
    prefix="/api/scan",
    tags=["Analyse de plantes"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Agent IA conversationnel"]
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics & Statistiques"]
)

app.include_router(
    plants.router,
    prefix="/api/plants",
    tags=["Catalogue de plantes"]
)


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


@app.get("/", include_in_schema=False)
def read_root():
    """Page de démarrage — redirige vers /login via le bouton COMMENCER."""
    return FileResponse(os.path.join(FRONTEND_DIR, "splash.html"))

@app.get("/login", include_in_schema=False)
def login_page():
    """Page de connexion / inscription."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/scan", include_in_schema=False)
def scan_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "scan.html"))

@app.get("/rapport", include_in_schema=False)
def rapport_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "rapport.html"))

@app.get("/historique", include_in_schema=False)
def historique_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "historique.html"))

@app.get("/analytics", include_in_schema=False)
def analytics_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "analytics.html"))

@app.get("/verify-email", include_in_schema=False)
def verify_email_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "verify-email.html"))

@app.get("/reset-password", include_in_schema=False)
def reset_password_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "reset-password.html"))

@app.get("/profil", include_in_schema=False)
def profil_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "profil.html"))

@app.get("/catalogue", include_in_schema=False)
def catalogue_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "catalogue.html"))


from routers.auth import SECRET_KEY as _SECRET_KEY, ALGORITHM as _ALGORITHM
from database import get_db as _gdb
from models import Scan as _Scan, User as _User
import pathlib
from typing import Optional as _Optional
from jose import jwt as _jwt, JWTError as _JWTError
from sqlalchemy.orm import Session as _Session

def _serve_image(filename: str, token: _Optional[str], db: _Session):
    """
    Logique commune de service d'image avec authentification JWT.
    Accepte le token en query param (?token=...) car <img> ne peut pas
    envoyer de header Authorization.
    """
    safe_name = pathlib.Path(filename).name
    if safe_name != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide.")

    file_path = os.path.join(UPLOADS_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image introuvable.")

    if not token or token == "null":
        logger.warning(f"[UPLOADS] Token manquant ou null pour {safe_name}")
        raise HTTPException(status_code=401, detail="Token manquant.")
    try:
        payload = _jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide.")
    except _JWTError as e:
        logger.warning(f"[UPLOADS] JWT invalide pour {safe_name} : {e}")
        raise HTTPException(status_code=401, detail="Token invalide ou expiré.")

    user = db.query(_User).filter(_User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable.")

    scan = db.query(_Scan).filter(
        _Scan.image_path.contains(safe_name),
        _Scan.user_id == user.id
    ).first()

    admin_email = os.getenv("ADMIN_EMAIL", "")
    is_admin = bool(admin_email and user.email.lower() == admin_email.lower())

    if not scan and not is_admin:
        raise HTTPException(status_code=403, detail="Accès refusé.")

    return FileResponse(file_path, media_type="image/jpeg")


@app.get("/api/uploads/{filename}", tags=["Fichiers"])
def serve_upload_file(
    filename: str,
    token: _Optional[str] = None,
    db: _Session = Depends(_gdb),
):
    """Sert une image uploadée (chemin api/uploads/). Requiert un JWT en ?token=."""
    return _serve_image(filename, token, db)


@app.get("/uploads/{filename}", include_in_schema=False)
def serve_upload_file_legacy(
    filename: str,
    token: _Optional[str] = None,
    db: _Session = Depends(_gdb),
):
    """Compatibilité avec les anciens scans dont image_path = 'uploads/...'."""
    return _serve_image(filename, token, db)


@app.get("/api/health", tags=["Système"])
def health_check():
    """
    Vérifier que l'API fonctionne.
    Renvoie un simple message de confirmation.
    """
    return {"status": "ok", "message": "MikiPlants API fonctionne correctement !"}

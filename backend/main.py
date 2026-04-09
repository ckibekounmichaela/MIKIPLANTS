# ============================================================
# FICHIER : backend/main.py
# RÔLE    : Point d'entrée principal de l'application FastAPI
#
# COMMENT LANCER L'APPLICATION :
#   1. Se placer dans le dossier backend : cd backend
#   2. Lancer le serveur : uvicorn main:app --reload
#   3. Ouvrir le navigateur sur : http://localhost:8000
#   4. Documentation API auto : http://localhost:8000/docs
#
# --reload : recharge automatiquement quand tu modifies le code
# ============================================================

import os
from dotenv import load_dotenv

# load_dotenv() DOIT être appelé EN PREMIER, avant tous les autres imports
# car les modules comme scan.py lisent os.getenv() au moment de leur import
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importer la configuration de la base de données
from database import engine, Base

# Importer tous les routers (groupes d'endpoints)
from routers import auth, scan, chat, analytics, plants

# -------------------------------------------------------
# Créer toutes les tables dans SQLite au démarrage
# Si les tables existent déjà, elles ne sont pas recréées
# -------------------------------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------------------------------
# Créer le dossier "uploads" si il n'existe pas
# C'est là qu'on stockera les images uploadées
# -------------------------------------------------------
os.makedirs("../uploads", exist_ok=True)

# -------------------------------------------------------
# Initialiser l'application FastAPI
# title et description apparaissent dans la doc auto (/docs)
# -------------------------------------------------------
app = FastAPI(
    title="WhatAPlant API",
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

# -------------------------------------------------------
# Handler d'erreurs de validation (422) — log les détails
# -------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.warning(f"[422] Validation échouée sur {request.method} {request.url.path}")
    logger.warning(f"[422] Body reçu : {body.decode('utf-8', errors='replace')}")
    logger.warning(f"[422] Erreurs   : {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# -------------------------------------------------------
# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend (HTML/JS) d'appeler l'API
# Sans cela, le navigateur bloquerait les requêtes
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # En production, remplacer par votre domaine
    allow_credentials=True,
    allow_methods=["*"],        # GET, POST, PUT, DELETE...
    allow_headers=["*"],
)

# -------------------------------------------------------
# Inclure les routers avec leurs préfixes d'URL
#
# Exemple avec prefix="/api/auth" :
#   auth.py définit POST "/login"
#   → l'URL finale sera POST "/api/auth/login"
# -------------------------------------------------------
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

# -------------------------------------------------------
# Servir les fichiers statiques (frontend HTML/CSS/JS)
# StaticFiles permet à FastAPI de servir des fichiers
# comme le ferait un serveur web classique (Apache, Nginx)
# -------------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory="../frontend"),
    name="static"
)

# Servir les images uploadées
app.mount(
    "/uploads",
    StaticFiles(directory="../uploads"),
    name="uploads"
)

# -------------------------------------------------------
# Route racine : page de démarrage (splash screen)
# -------------------------------------------------------
@app.get("/", include_in_schema=False)
def read_root():
    """Page de démarrage — redirige vers /login via le bouton COMMENCER."""
    return FileResponse("../frontend/splash.html")

@app.get("/login", include_in_schema=False)
def login_page():
    """Page de connexion / inscription."""
    return FileResponse("../frontend/index.html")


# -------------------------------------------------------
# Routes pour les pages HTML (navigation directe par URL)
# -------------------------------------------------------
@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse("../frontend/dashboard.html")

@app.get("/scan", include_in_schema=False)
def scan_page():
    return FileResponse("../frontend/scan.html")

@app.get("/rapport", include_in_schema=False)
def rapport_page():
    return FileResponse("../frontend/rapport.html")

@app.get("/historique", include_in_schema=False)
def historique_page():
    return FileResponse("../frontend/historique.html")

@app.get("/analytics", include_in_schema=False)
def analytics_page():
    return FileResponse("../frontend/analytics.html")

@app.get("/verify-email", include_in_schema=False)
def verify_email_page():
    return FileResponse("../frontend/verify-email.html")

@app.get("/reset-password", include_in_schema=False)
def reset_password_page():
    return FileResponse("../frontend/reset-password.html")

@app.get("/profil", include_in_schema=False)
def profil_page():
    return FileResponse("../frontend/profil.html")


# -------------------------------------------------------
# Endpoint de vérification de santé de l'API
# Utile pour tester si le serveur tourne correctement
# -------------------------------------------------------
@app.get("/api/health", tags=["Système"])
def health_check():
    """
    Vérifier que l'API fonctionne.
    Renvoie un simple message de confirmation.
    """
    return {"status": "ok", "message": "WhatAPlant API fonctionne correctement !"}

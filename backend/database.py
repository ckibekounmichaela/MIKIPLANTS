# ============================================================
# FICHIER : backend/database.py
# RÔLE    : Configuration de la connexion à la base de données SQLite
#
# CONCEPT POUR DÉBUTANT :
#   SQLAlchemy est un ORM (Object Relational Mapper).
#   Cela signifie qu'on peut manipuler la base de données
#   en écrivant du Python, sans écrire du SQL directement.
#   Ex: au lieu de "SELECT * FROM users", on écrit User.query.all()
# ============================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# -------------------------------------------------------
# URL de connexion à MySQL (XAMPP)
# Format : mysql+pymysql://utilisateur:motdepasse@hote/nom_base
# Par défaut XAMPP : root sans mot de passe, port 3306
# -------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Railway / Render fournissent des URLs PostgreSQL en "postgres://" mais
# SQLAlchemy requiert "postgresql://" — on corrige automatiquement
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# -------------------------------------------------------
# Fallback : construire l'URL depuis les variables PG individuelles
# (plus fiable que copier une URL complète sur Railway)
# -------------------------------------------------------
if not DATABASE_URL or "://" not in DATABASE_URL:
    pg_user = os.getenv("PGUSER", "postgres")
    pg_password = os.getenv("PGPASSWORD", "")
    pg_host = os.getenv("PGHOST", "")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db   = os.getenv("PGDATABASE", "railway")

    if pg_host and pg_password:
        import urllib.parse
        DATABASE_URL = (
            f"postgresql://{urllib.parse.quote_plus(pg_user)}"
            f":{urllib.parse.quote_plus(pg_password)}"
            f"@{pg_host}:{pg_port}/{pg_db}"
        )

# Dernier recours : MySQL local (développement)
if not DATABASE_URL or "://" not in DATABASE_URL:
    DATABASE_URL = "mysql+pymysql://root:@localhost/mikiplants"

# -------------------------------------------------------
# Créer le "moteur" de connexion
# Pour les connexions internes Railway (.railway.internal)
# le SSL n'est pas requis
# -------------------------------------------------------
is_postgres = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")
is_internal = "railway.internal" in DATABASE_URL

if is_postgres:
    connect_args = {} if is_internal else {"sslmode": "require"}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    engine = create_engine(DATABASE_URL)

# -------------------------------------------------------
# SessionLocal : Une "session" est comme une connexion
# temporaire à la base de données pour effectuer des opérations
# autocommit=False → les changements ne sont pas sauvegardés
#                    automatiquement (on doit appeler db.commit())
# autoflush=False  → les données ne sont pas envoyées à la BD
#                    avant qu'on le demande explicitement
# -------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------------------------------------
# Base : classe parente de tous nos modèles (tables)
# Chaque modèle (User, Scan, etc.) va hériter de cette Base
# -------------------------------------------------------
Base = declarative_base()


def get_db():
    """
    Fonction générateur qui fournit une session de base de données.

    CONCEPT POUR DÉBUTANT :
    Cette fonction est utilisée comme "dépendance" dans FastAPI.
    Elle ouvre une connexion, l'utilise, puis la ferme automatiquement,
    même si une erreur se produit (grâce au bloc finally).

    Exemple d'utilisation dans un router :
        @app.get("/plantes")
        def liste_plantes(db: Session = Depends(get_db)):
            return db.query(Plante).all()
    """
    # Créer une nouvelle session
    db = SessionLocal()
    try:
        # Fournir la session au code qui en a besoin
        yield db
    finally:
        # Toujours fermer la session après utilisation
        # Le mot "finally" garantit que c'est exécuté même en cas d'erreur
        db.close()

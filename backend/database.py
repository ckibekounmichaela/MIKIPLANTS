import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()


import urllib.parse

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Corriger le préfixe mysql:// → mysql+pymysql:// (Railway MySQL)
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

if not DATABASE_URL or "://" not in DATABASE_URL:
    mysql_host     = os.getenv("MYSQLHOST", os.getenv("MYSQL_HOST", ""))
    mysql_port     = os.getenv("MYSQLPORT", os.getenv("MYSQL_PORT", "3306"))
    mysql_user     = os.getenv("MYSQLUSER", os.getenv("MYSQL_USER", "root"))
    mysql_password = os.getenv("MYSQLPASSWORD", os.getenv("MYSQL_PASSWORD", ""))
    mysql_db       = os.getenv("MYSQLDATABASE", os.getenv("MYSQL_DATABASE", "railway"))

    if mysql_host and mysql_password:
        DATABASE_URL = (
            f"mysql+pymysql://{urllib.parse.quote_plus(mysql_user)}"
            f":{urllib.parse.quote_plus(mysql_password)}"
            f"@{mysql_host}:{mysql_port}/{mysql_db}"
        )

# Fallback : variables PostgreSQL individuelles de Railway
if not DATABASE_URL or "://" not in DATABASE_URL:
    pg_user     = os.getenv("PGUSER", "postgres")
    pg_password = os.getenv("PGPASSWORD", "")
    pg_host     = os.getenv("PGHOST", "")
    pg_port     = os.getenv("PGPORT", "5432")
    pg_db       = os.getenv("PGDATABASE", "railway")

    if pg_host and pg_password:
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
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,       # Teste la connexion avant de l'utiliser depuis le pool
        pool_recycle=1800,        # Recycle les connexions toutes les 30 min (avant le timeout MySQL/PG)
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,       # Évite l'erreur e3q8 "invalid transaction"
        pool_recycle=1800,        # Recycle avant le wait_timeout MySQL (défaut 8h)
        pool_size=5,              # Nombre de connexions maintenues en pool
        max_overflow=10,          # Connexions supplémentaires autorisées en pic
        connect_args={
            "connect_timeout": 10,    # Timeout connexion 10s (évite de bloquer indéfiniment)
        },
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

        db.close()

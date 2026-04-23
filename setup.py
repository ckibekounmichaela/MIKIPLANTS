import sys
import os
import subprocess
import shutil

# Dossier racine du projet (dossier ou se trouve ce script)
ROOT = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    VENV_PYTHON = os.path.join(ROOT, "venv", "Scripts", "python.exe")
    VENV_PIP    = os.path.join(ROOT, "venv", "Scripts", "pip.exe")
else:
    VENV_PYTHON = os.path.join(ROOT, "venv", "bin", "python")
    VENV_PIP    = os.path.join(ROOT, "venv", "bin", "pip")


def print_header():
    print()
    print("=" * 50)
    print("   MikiPlants - Installation automatique")
    print("=" * 50)
    print()


def print_step(num, total, message):
    print(f"[{num}/{7}] {message}...")


def print_ok(message):
    print(f"  OK  - {message}")


def print_info(message):
    print(f"  --> {message}")


def print_error(message):
    print(f"  ERREUR : {message}")


def check_python_version():
    """Verifier que Python 3.10 ou plus recent est installe."""
    print_step(1, 6, "Verification de Python")

    version = sys.version_info
    print_ok(f"Python {version.major}.{version.minor}.{version.micro} detecte")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error("Python 3.10 minimum requis.")
        print_info("Telechargez Python sur https://www.python.org/downloads/")
        sys.exit(1)

    print()


def create_venv():
    """Creer l'environnement virtuel si il n'existe pas."""
    print_step(2, 6, "Creation de l'environnement virtuel")

    venv_dir = os.path.join(ROOT, "venv")

    if os.path.exists(venv_dir):
        print_info("L'environnement virtuel existe deja, conserve.")
    else:
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print_error("Impossible de creer le venv.")
            print(result.stderr)
            sys.exit(1)
        print_ok("Environnement virtuel cree dans venv/")

    print()


def upgrade_pip():
    """Mettre a jour pip vers la derniere version."""
    print_step(3, 6, "Mise a jour de pip")

    result = subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        capture_output=True,
        text=True
    )
    print_ok("pip mis a jour")
    print()


def install_dependencies():
    """Installer toutes les dependances depuis requirements.txt."""
    print_step(4, 6, "Installation des dependances Python")
    print_info("Patientez, cela peut prendre quelques minutes...")
    print()

    requirements_file = os.path.join(ROOT, "requirements.txt")

    if not os.path.exists(requirements_file):
        print_error("requirements.txt introuvable.")
        sys.exit(1)

    result = subprocess.run(
        [VENV_PIP, "install", "-r", requirements_file],
        cwd=ROOT
    )

    if result.returncode != 0:
        print_error("L'installation a echoue.")
        print_info("Verifiez votre connexion internet.")
        sys.exit(1)

    print()
    print_ok("Toutes les dependances sont installees")
    print()


def create_env_file():
    """Creer le fichier .env depuis .env.example si inexistant."""
    print_step(5, 6, "Configuration du fichier .env")

    env_file     = os.path.join(ROOT, ".env")
    env_example  = os.path.join(ROOT, ".env.example")

    if os.path.exists(env_file):
        print_info(".env existe deja, non ecrase.")
    elif os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print_ok(".env cree depuis .env.example")
        print()
        print("  IMPORTANT : Ouvrez .env et renseignez vos cles API :")
        print("    PLANTNET_API_KEY  -> https://my.plantnet.org/")
        print("    GROQ_API_KEY      -> https://console.groq.com/")
        print("    SECRET_KEY        -> une longue chaine aleatoire")
    else:
        print_info(".env.example introuvable. Creez .env manuellement.")

    print()


def create_folders():
    """Creer les dossiers necessaires au projet."""
    print_step(6, 7, "Creation des dossiers")

    uploads_dir = os.path.join(ROOT, "uploads")

    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print_ok("Dossier uploads/ cree")
    else:
        print_info("Dossier uploads/ existe deja")

    print()


def init_database():
    """Creer les tables SQLite et le compte par defaut."""
    print_step(7, 7, "Initialisation de la base de donnees")

    init_script = os.path.join(ROOT, "backend", "init_db.py")

    result = subprocess.run(
        [VENV_PYTHON, init_script],
        cwd=os.path.join(ROOT, "backend")
    )

    if result.returncode != 0:
        print_error("Initialisation de la base de donnees echouee.")
        sys.exit(1)

    print()


def print_summary():
    """Afficher les instructions finales."""
    print("=" * 50)
    print("   Installation terminee avec succes !")
    print("=" * 50)
    print()
    print("  Etapes suivantes :")
    print()
    print("  1. Ouvrez .env et renseignez vos cles API :")
    print("     PLANTNET_API_KEY -> https://my.plantnet.org/")
    print("     GROQ_API_KEY     -> https://console.groq.com/")
    print("     SECRET_KEY       -> n'importe quelle longue chaine")
    print()
    print("  2. Lancez le serveur : double-cliquez sur start.bat")
    print()
    print("  3. Connectez-vous sur http://localhost:8000 avec :")
    print("     Email        : admin@mikiplants.com")
    print("     Mot de passe : admin123")
    print()
    print("=" * 50)
    print()


if __name__ == "__main__":
    print_header()
    check_python_version()
    create_venv()
    upgrade_pip()
    install_dependencies()
    create_env_file()
    create_folders()
    init_database()
    print_summary()

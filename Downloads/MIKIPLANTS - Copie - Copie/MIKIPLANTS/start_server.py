# ============================================================
# FICHIER : start_server.py
# ROLE    : Demarrer le serveur WhatAPlant
#
# USAGE   : python start_server.py
#           OU double-cliquer sur start.bat
#
# CE QUE CE SCRIPT FAIT :
#   1. Verifie que l'installation a ete faite (venv existe)
#   2. Verifie que .env est present
#   3. Avertit si les cles API ne sont pas configurees
#   4. Ouvre le navigateur automatiquement
#   5. Lance le serveur uvicorn via le venv
# ============================================================

import sys
import os
import subprocess
import time
import threading
import webbrowser

# Dossier racine du projet
ROOT    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")

# Executable uvicorn dans le venv
if sys.platform == "win32":
    UVICORN = os.path.join(ROOT, "venv", "Scripts", "uvicorn.exe")
else:
    UVICORN = os.path.join(ROOT, "venv", "bin", "uvicorn")

APP_URL = "http://localhost:8000"


def print_header():
    print()
    print("=" * 50)
    print("   WhatAPlant - Demarrage du serveur")
    print("=" * 50)
    print()


def check_venv():
    """Verifier que le venv et uvicorn sont installes."""
    if not os.path.exists(UVICORN):
        print("  ERREUR : Environnement virtuel introuvable.")
        print()
        print("  Lancez d'abord install.bat pour installer le projet.")
        print()
        input("  Appuyez sur Entree pour fermer...")
        sys.exit(1)


def check_env_file():
    """Verifier que le fichier .env existe."""
    env_file = os.path.join(ROOT, ".env")

    if not os.path.exists(env_file):
        print("  ERREUR : Fichier .env manquant.")
        print()
        print("  Copiez .env.example en .env et remplissez vos cles API.")
        print()
        input("  Appuyez sur Entree pour fermer...")
        sys.exit(1)


def check_api_keys():
    """Avertir si les cles API ne sont pas configurees."""
    env_file = os.path.join(ROOT, ".env")

    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()

    warned = False

    if "votre_cle_plantnet_ici" in content:
        print("  ATTENTION : PLANTNET_API_KEY non configuree.")
        print("  Obtenez votre cle sur : https://my.plantnet.org/")
        print()
        warned = True

    if "votre_cle_groq_ici" in content:
        print("  ATTENTION : GROQ_API_KEY non configuree.")
        print("  Obtenez votre cle sur : https://console.groq.com/")
        print()
        warned = True

    if "remplacer_par_une_cle_secrete" in content:
        print("  ATTENTION : SECRET_KEY non configuree dans .env")
        print()
        warned = True

    # Si des cles manquent, attendre 3s avant de continuer
    if warned:
        print("  Le serveur va demarrer mais certaines fonctions")
        print("  ne fonctionneront pas sans les cles API.")
        print()
        time.sleep(3)


def open_browser_delayed(delay=2):
    """
    Ouvrir le navigateur apres un delai.
    Lance dans un thread separe pour ne pas bloquer le serveur.
    """
    def _open():
        time.sleep(delay)
        webbrowser.open(APP_URL)

    # threading.Thread permet d'executer du code en parallele
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def start_uvicorn():
    """Lancer le serveur uvicorn."""
    print("=" * 50)
    print("   Serveur WhatAPlant demarre !")
    print()
    print(f"   Acces local   : {APP_URL}")
    print(f"   Documentation : {APP_URL}/docs")
    print()
    print("   Pour arreter le serveur : CTRL + C")
    print("=" * 50)
    print()

    # subprocess.run() avec le chemin absolu vers uvicorn du venv
    # Avantage : pas besoin d'activer le venv manuellement
    result = subprocess.run(
        [
            UVICORN,
            "main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ],
        cwd=BACKEND   # Executer depuis le dossier backend/
    )

    # Ce code s'execute apres l'arret du serveur
    print()
    print("  Le serveur s'est arrete.")


# ============================================================
# POINT D'ENTREE
# ============================================================
if __name__ == "__main__":
    print_header()
    check_venv()
    check_env_file()
    check_api_keys()

    print("  Ouverture du navigateur dans 2 secondes...")
    print()
    open_browser_delayed(delay=2)

    start_uvicorn()

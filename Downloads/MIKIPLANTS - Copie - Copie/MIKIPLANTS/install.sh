#!/bin/bash
# ============================================================
# FICHIER : install.sh
# RÔLE    : Script d'installation automatique pour Linux / macOS
#
# COMMENT L'UTILISER :
#   1. Rendre le script exécutable (une seule fois) :
#      chmod +x install.sh
#   2. Lancer l'installation :
#      ./install.sh
# ============================================================

# "set -e" : arrêter le script si une commande échoue
set -e

# Couleurs pour les messages dans le terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'   # NC = No Color (réinitialiser la couleur)

# Fonctions utilitaires pour afficher des messages colorés
ok()      { echo -e "${GREEN} OK${NC} - $1"; }
info()    { echo -e "${BLUE} INFO${NC} - $1"; }
warn()    { echo -e "${YELLOW} ATTENTION${NC} - $1"; }
error()   { echo -e "${RED} ERREUR${NC} - $1"; exit 1; }

echo ""
echo "============================================================"
echo "   WhatAPlant - Installation automatique (Linux/macOS)"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# ETAPE 1 : Vérifier Python 3
# ------------------------------------------------------------
echo "[1/6] Vérification de Python..."

# Chercher python3 ou python selon le système
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    error "Python n'est pas installé.\nInstallez-le avec votre gestionnaire de paquets :\n  Ubuntu/Debian : sudo apt install python3\n  macOS         : brew install python3"
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
ok "$PYTHON_VERSION détecté"
echo ""

# ------------------------------------------------------------
# ETAPE 2 : Créer l'environnement virtuel
# ------------------------------------------------------------
echo "[2/6] Création de l'environnement virtuel..."

if [ -d "venv" ]; then
    info "L'environnement virtuel existe déjà, on le conserve."
else
    $PYTHON -m venv venv || error "Impossible de créer le venv.\nInstallez python3-venv : sudo apt install python3-venv"
    ok "Environnement virtuel créé dans 'venv/'"
fi
echo ""

# ------------------------------------------------------------
# ETAPE 3 : Activer l'environnement virtuel
# ------------------------------------------------------------
echo "[3/6] Activation de l'environnement virtuel..."
source venv/bin/activate || error "Impossible d'activer le venv."
ok "Environnement virtuel activé"
echo ""

# ------------------------------------------------------------
# ETAPE 4 : Installer les dépendances
# ------------------------------------------------------------
echo "[4/6] Installation des dépendances Python..."
echo "  (Cela peut prendre quelques minutes...)"
echo ""

python -m pip install --upgrade pip --quiet
echo "  pip mis à jour"

pip install -r requirements.txt || error "L'installation des dépendances a échoué."
echo ""
ok "Toutes les dépendances sont installées"
echo ""

# ------------------------------------------------------------
# ETAPE 5 : Créer le fichier .env
# ------------------------------------------------------------
echo "[5/6] Configuration du fichier .env..."

if [ -f ".env" ]; then
    info "Le fichier .env existe déjà, on ne l'écrase pas."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        ok "Fichier .env créé depuis le modèle .env.example"
        echo ""
        warn "IMPORTANT : Éditez .env et remplissez vos clés API :"
        warn "  - PLANTNET_API_KEY  → https://my.plantnet.org/"
        warn "  - GROQ_API_KEY      → https://console.groq.com/"
        warn "  - SECRET_KEY        → une chaîne aléatoire longue"
    else
        warn ".env.example introuvable, créez .env manuellement"
    fi
fi
echo ""

# ------------------------------------------------------------
# ETAPE 6 : Créer les dossiers nécessaires
# ------------------------------------------------------------
echo "[6/6] Création des dossiers..."

mkdir -p uploads
ok "Dossier 'uploads/' prêt"
echo ""

# ------------------------------------------------------------
# RÉSUMÉ FINAL
# ------------------------------------------------------------
echo "============================================================"
echo "   Installation terminée avec succès !"
echo "============================================================"
echo ""
echo "  ÉTAPES SUIVANTES :"
echo ""
echo "  1. Éditez le fichier .env :"
echo "     nano .env   OU   code .env"
echo ""
echo "  2. Lancez l'application :"
echo "     ./start.sh"
echo ""
echo "  3. Ouvrez votre navigateur sur :"
echo "     http://localhost:8000"
echo ""
echo "============================================================"
echo ""

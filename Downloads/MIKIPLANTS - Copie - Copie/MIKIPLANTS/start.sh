#!/bin/bash
# ============================================================
# FICHIER : start.sh
# RÔLE    : Démarrer le backend WhatAPlant (Linux/macOS)
#
# COMMENT L'UTILISER :
#   1. Rendre exécutable (une seule fois) : chmod +x start.sh
#   2. Lancer le serveur : ./start.sh
#
# PRÉREQUIS :
#   Avoir exécuté ./install.sh et rempli le fichier .env
# ============================================================

set -e

# Couleurs
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

ok()   { echo -e "${GREEN} OK${NC} - $1"; }
warn() { echo -e "${YELLOW} ATTENTION${NC} - $1"; }
err()  { echo -e "${RED} ERREUR${NC} - $1"; exit 1; }

echo ""
echo "============================================================"
echo "   WhatAPlant - Démarrage du serveur"
echo "============================================================"
echo ""

# Vérifier que le venv existe
[ -d "venv" ] || err "Environnement virtuel manquant. Exécutez ./install.sh d'abord."

# Vérifier que .env existe
[ -f ".env" ] || err "Fichier .env manquant. Copiez .env.example en .env et remplissez les clés."

# Vérifications des clés API
if grep -q "votre_cle_plantnet_ici" .env 2>/dev/null; then
    warn "PLANTNET_API_KEY n'est pas configurée → https://my.plantnet.org/"
fi
if grep -q "votre_cle_groq_ici" .env 2>/dev/null; then
    warn "GROQ_API_KEY n'est pas configurée → https://console.groq.com/"
fi

# Activer le venv
source venv/bin/activate
ok "Environnement virtuel activé"

# Aller dans le dossier backend
cd backend

# Ouvrir le navigateur (selon le système)
echo "  Ouverture du navigateur..."
sleep 1
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8000 &    # Linux
elif command -v open &>/dev/null; then
    open http://localhost:8000 &        # macOS
fi

echo ""
echo "============================================================"
echo -e "   ${GREEN}Serveur WhatAPlant en cours de démarrage...${NC}"
echo ""
echo -e "   URL locale    : ${CYAN}http://localhost:8000${NC}"
echo -e "   Documentation : ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo "   Pour arrêter : CTRL + C"
echo "============================================================"
echo ""

# Lancer uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

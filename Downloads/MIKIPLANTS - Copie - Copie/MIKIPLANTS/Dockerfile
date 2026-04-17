FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Créer un faux exécutable "cd" qui lance uvicorn
# Railway essaie d'exécuter "cd backend && uvicorn..." comme binaire
# Ce script intercepte l'appel et démarre l'app correctement
RUN printf '#!/bin/sh\nexec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}\n' \
    > /usr/local/bin/cd && chmod +x /usr/local/bin/cd

WORKDIR /app/backend

EXPOSE 8000

FROM python:3.11-slim

# Cache bust
ARG CACHEBUST=2

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le projet
COPY . .

# Créer un faux exécutable "cd" qui lance uvicorn
# Railway tente d'exécuter "cd backend && uvicorn..." comme binaire
# Ce script intercepte l'appel et démarre l'app avec le bon port
RUN python3 -c "
lines = ['#!/bin/sh\n', 'exec uvicorn main:app --host 0.0.0.0 --port \$PORT\n']
open('/usr/local/bin/cd', 'w').writelines(lines)
" && chmod +x /usr/local/bin/cd

WORKDIR /app/backend

EXPOSE 8000

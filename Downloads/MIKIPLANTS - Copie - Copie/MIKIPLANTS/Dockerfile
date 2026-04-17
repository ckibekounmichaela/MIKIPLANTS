FROM python:3.11-slim

# Aller directement dans le dossier backend comme WORKDIR
WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Se placer dans backend pour le démarrage
WORKDIR /app/backend

# Exposer le port
EXPOSE 8000

# Démarrer uvicorn directement (sans cd)
ENTRYPOINT ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
